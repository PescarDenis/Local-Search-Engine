import re
import itertools
from abc import ABC, abstractmethod

"""
Each decorator wraps a QueryBuilder and transforms the raw user input
before it reaches the QueryParser.

The working mode is :
WildcardDecorator(SynonymDecorator(SanitizationDecorator(BaseQueryBuilder())))
Execution order: Sanitization -> Synonyms -> Wildcards
"""


class QueryBuilder(ABC):
    @abstractmethod
    #transform the raw query string and return the result
    def build(self, raw_query: str) -> str:
        pass

class BaseQueryBuilder(QueryBuilder):
    def build(self, raw_query: str) -> str:
        return raw_query

class QueryDecorator(QueryBuilder):
    def __init__(self, wrapped: QueryBuilder) -> None:
        self._wrapped = wrapped

    def build(self, raw_query: str) -> str:
        return self._wrapped.build(raw_query)


#Strips characters that could break FTS5 syntax.
#Preserves quoted phrases and qualifier prefixes (path:, content:, color:)

#characters that are dangerous for FTS5 when used outside of intentional syntax
DANGEROUS_CHARS = re.compile(r'[^\w\s":*\-.]', re.UNICODE)

PATTERN = re.compile(r'^(path|content|color):(.+)$', re.IGNORECASE)

#matches a plain word that is not a qualifier, not quoted, not OR
PLAIN_TERM = re.compile(r'^[a-zA-Z0-9_\-.]+$')

"""
    Quote split: keeps text inside quotes grouped as one token.
    Unlike a normal .split() which  cuts at every space, this function
    uses a toggle switch (in_quotes) to ignore spaces that are inside quotes.

    Example:
        raw = 'content:"img by" test'
        returns: ['content:"img by"', 'test']
"""
def _tokenize(raw: str) -> list[str]:
    tokens, current, in_quotes = [], [], False

    for char in raw:
        if char == '"':
            in_quotes = not in_quotes #flip the switch when we see a quote

        #if we see a spacr and we are not inside quotes, cut the word here
        if char == ' ' and not in_quotes:
            if current:
                tokens.append("".join(current))
                current.clear()
        else:
            #otherwise just keep building the current word letter by letter
            current.append(char)
            
    #grab whatever word was left over at the end of the sentence
    if current:
        tokens.append("".join(current))
        
    return tokens


class SanitizationDecorator(QueryDecorator):


    def build(self, raw_query: str) -> str:
        query = self._wrapped.build(raw_query)
        tokens = _tokenize(query)
        cleaned = []
        #iterate through the tokens
        for token in tokens:
            if PATTERN.match(token):
                #keep qualifier prefix intact, sanitize only the value part
                prefix, value = token.split(":", 1)
                value = DANGEROUS_CHARS.sub("", value) #strip the chars only from the value part, what the user actually inserts
                cleaned.append(f"{prefix}:{value}" if value else prefix + ":")
            elif token.startswith('"') and token.endswith('"'):
                #keep quoted phrases, only strip dangerous chars inside
                inner = DANGEROUS_CHARS.sub("", token[1:-1])
                cleaned.append(f'"{inner}"' if inner else "")
            else:
                #else strip the simple generic terms outside of the pattern matching,delete the unwanted terms
                cleaned.append(DANGEROUS_CHARS.sub("", token))

        return " ".join(t for t in cleaned if t)


class SynonymDecorator(QueryDecorator):

    #simple dictionary of possible synonyms
    SYNONYMS: dict[str, list[str]] = {
        "img":    ["img", "image", "photo","images"],
        "pic":    ["pic", "picture", "photo", "image"],
        "doc":    ["doc", "document", "file"],
        "docs":   ["docs", "documents", "files"],
        "log":    ["log", "logs", "logging"],
        "config": ["config", "configuration", "settings"],
        "src":    ["src", "source", "code"],
        "lib":    ["lib", "library", "libraries"],
        "test":   ["test", "tests", "testing"],
        "err":    ["err", "error", "errors"],
    }

    def _expand_phrase(self, phrase: str) -> list[str]:
        #split phrase into words
        #get synonyms for each word or just the word itself if no synonyms exist
        #Example: "img doc" -> opts = [["img", "image", "photo", "images"], ["doc", "document", "file"]]
        opts = [self.SYNONYMS.get(w, [w]) for w in phrase.split()]
        if not opts:
            return [phrase]
            
        #generate the Cartesian product all possible combinations of the words
        #itertools.product(*opts) takes one word from the first list, one from the second, etc.
        #Example: "img doc", "img document", "image doc", etc.
        return [" ".join(comb) for comb in itertools.product(*opts)]

    def build(self, raw_query: str) -> str:
        #run the previous decorators
        query = self._wrapped.build(raw_query)
        #split the query safely
        tokens = _tokenize(query)
        expanded = []

        #check each token one by one
        for token in tokens:
            match = PATTERN.match(token)
            if match:
                #qualifier token content:"img by"
                prefix = match.group(1) # "content"
                value = match.group(2).strip('"') # "img by"
                phrases = self._expand_phrase(value)
                
                #if no synonyms were found, keep the token exactly as it was
                if len(phrases) == 1 and phrases[0] == value:
                    expanded.append(token)
                else:
                    #produce multiple qualifier tokens so the parser will OR them together
                    #content:"img by" content:"image by" ...
                    for phrase in phrases:
                        expanded.append(f'{prefix}:"{phrase}"')
                        
            elif token.startswith('"') and token.endswith('"'):
                #standalone quoted phrase "img doc"
                value = token.strip('"')
                phrases = self._expand_phrase(value)
                if len(phrases) == 1 and phrases[0] == value:
                    expanded.append(token)
                else:
                    #format as an OR group: "img doc" OR "image doc" ...
                    alternatives = [f'"{p}"' for p in phrases]
                    expanded.append(f"({' OR '.join(alternatives)})")
                    
            else:
                #plain term
                phrases = self._expand_phrase(token)
                if len(phrases) == 1 and phrases[0]== token:
                    expanded.append(token)
                else:
                    expanded.append(f"({' OR '.join(phrases)})")

        return " ".join(expanded)


"""" 
Appends * to plain terms for prefix matching.
Skips quoted phrases, qualifier values, OR groups, and terms already ending with *.
"""
class WildcardDecorator(QueryDecorator):

    def build(self, raw_query: str) -> str:
        query = self._wrapped.build(raw_query)

        #process while respecting quoted sections and OR groups
        result = []
        i = 0
        chars = query

        while i < len(chars):
            #skip quoted phrases
            if chars[i] == '"':
                end = chars.find('"', i + 1)
                if end == -1:
                    result.append(chars[i:])
                    break
                result.append(chars[i:end + 1])
                i = end + 1
                continue

            #skip OR groups
            if chars[i] == '(':
                end = chars.find(')', i + 1)
                if end == -1:
                    result.append(chars[i:])
                    break
                result.append(chars[i:end + 1])
                i = end + 1
                continue

            #collect a token non-space sequence
            if chars[i] != ' ':
                start = i
                while i < len(chars) and chars[i] != ' ':
                    i += 1
                token = chars[start:i]

                #skip qualifiers and already wildcarded terms
                if PATTERN.match(token):
                    result.append(token)
                elif token.endswith('*'):
                    result.append(token)
                elif PLAIN_TERM.match(token):
                    result.append(f"{token}*")
                else:
                    result.append(token)
                continue

            result.append(chars[i])
            i += 1

        return "".join(result)
