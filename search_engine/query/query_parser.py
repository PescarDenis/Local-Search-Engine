import re
from collections import defaultdict
#sanitization of FTS special characters is handled by the SanitizationDecorator
#matches targeted searches like path:some_folder, content:text, or color:red
PATTERN = re.compile(r'^(path|content|color):(.+)$', re.IGNORECASE)

class QueryParser:
    def parse(self, raw: str) -> str | None:
        raw = raw.strip()
        if not raw:
            return None

        fields = defaultdict(list)
        general_terms = []

        #sort tokens into specific fields (path:) or general search terms
        for token in self._tokenize(raw):
            match = PATTERN.match(token)
            if match:
                key, val = match.group(1).lower(), self._clean_term(match.group(2))
                if val:
                    fields[key].append(val)
            else:
                cleaned = self._clean_term(token)
                if cleaned:
                    general_terms.append(cleaned)

        parts = []

        #build query clauses for standard columns
        for key in ("path", "content", "color"):
            vals = fields.get(key)
            if vals:
                parts.append(self._build_filter(key, vals))

        #add any plain text search terms at the end
        if general_terms:
            parts.append(" ".join(general_terms))

        #combine all parts with AND logic, returning none if the query is empty
        return " AND ".join(parts) if parts else None

    def _tokenize(self, raw: str) -> list[str]:
        #splits the raw string by spaces, but keeps text inside quotes grouped together
        tokens, current, in_quotes = [], [], False

        for char in raw:
            if char == '"':
                in_quotes = not in_quotes
            if char == ' ' and not in_quotes:
                if current:
                    tokens.append("".join(current))
                    current.clear()
            else:
                current.append(char)

        if current:
            tokens.append("".join(current))

        return tokens

    def _clean_term(self, value: str) -> str:
        #check if the input is in between quotes
        is_quoted = value.startswith('"') and value.endswith('"') and len(value) >= 2
        #extract the inner content safely
        if is_quoted:
            cleaned = value[1:-1].strip()
            return f'"{cleaned}"' if cleaned else ""
        return value.strip()

    def _build_filter(self, column: str, values: list[str]) -> str:
        #formats a column search wrapping in parentheses if there are multiple values
        clauses = [f'{column} : {v}' if v.startswith('"') else f'{column} : "{v}"' for v in values]
        return clauses[0] if len(values) == 1 else f"({' OR '.join(clauses)})"