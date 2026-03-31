import re

_FTS5_REG = re.compile(r'["\(\)\*\:\^]')

class QueryParser:

    def parse(self, raw: str) -> str | None:
        cleaned = _FTS5_REG.sub("", raw).strip()

        if not cleaned:
            return None

        tokens = cleaned.split()
        if not tokens:
            return None

        return " ".join(tokens)
