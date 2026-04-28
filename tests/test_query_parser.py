from search_engine.query.query_parser import QueryParser

class TestQueryParser:

    def setup_method(self):
        self.parser = QueryParser()

    def test_plain_single_word(self):
        result = self.parser.parse("hello")
        assert result == "hello"

    def test_plain_multi_word(self):
        result = self.parser.parse("hello world")
        assert result == "hello world"

    def test_path_qualifier(self):
        result = self.parser.parse("path:src")
        assert result == 'path : "src"'

    def test_content_qualifier(self):
        result = self.parser.parse("content:TODO")
        assert result == 'content : "TODO"'

    def test_extension_treated_as_general(self):
        result = self.parser.parse("ext:py")
        assert result == "ext:py"

    def test_multiple_different_qualifiers(self):
        result = self.parser.parse("path:src content:TODO")
        assert result == 'path : "src" AND content : "TODO"'

    def test_duplicate_path_qualifiers_and_logic(self):
        result = self.parser.parse("path:src path:engine")
        assert result == '(path : "src" AND path : "engine")'

    def test_duplicate_content_qualifiers_and_logic(self):
        result = self.parser.parse("content:import content:os")
        assert result == '(content : "import" AND content : "os")'

    def test_qualifier_with_general_term(self):
        result = self.parser.parse("path:src hello")
        assert result == 'path : "src" AND hello'

    def test_all_qualifier_types_combined(self):
        result = self.parser.parse("path:src content:TODO")
        assert 'path : "src"' in result
        assert 'content : "TODO"' in result

    def test_quoted_value_in_qualifier(self):
        result = self.parser.parse('content:"hello world"')
        assert result == 'content : "hello world"'

    def test_empty_input_returns_none(self):
        assert self.parser.parse("") is None

    def test_whitespace_only_returns_none(self):
        assert self.parser.parse("   ") is None

    def test_fts5_special_chars_sanitized(self):
        result = self.parser.parse("he*llo(world)")
        assert result is not None
        assert "*" not in result
        assert "(" not in result
        assert ")" not in result

    def test_qualifier_with_empty_value_ignored(self):
        result = self.parser.parse('path: hello')
        assert result is not None

    def test_case_insensitive_qualifier_keys(self):
        result = self.parser.parse("PATH:src")
        assert result == 'path : "src"'

    def test_mixed_qualifiers_ordering(self):
        result = self.parser.parse("hello path:src world content:TODO")
        parts = result.split(" AND ")
        assert len(parts) == 3
        assert parts[0] == 'path : "src"'
        assert parts[1] == 'content : "TODO"'
        assert parts[2] == "hello world"
