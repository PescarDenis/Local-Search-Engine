from ..models import SearchResult

class ResultFormatter:
    def format(self, rows: list) -> list[SearchResult]:
        results = []
        for row in rows:
            try:
                preview = self._pick_preview(  row["snippet"], row["preview"])
                results.append(
                    SearchResult(
                        path=row["path"],
                        filename=row["filename"],
                        preview=preview,
                        modified_at=row["modified_at"],
                        score=row["combined_score"],
                    )
                )
            except (IndexError, KeyError, TypeError):
                continue
        return results
    #choose between the preview that is generated from each txt file
    #or the snippet FTS is given
    def _pick_preview(self, snippet: str | None, preview: str | None) -> str:
        if snippet:
            cleaned = self._clean_snippet(snippet)
            if cleaned:
                return cleaned
        if preview:
            return preview.strip()
        return ""
    #function to clean the preview -> more clear output in the CLI
    def _clean_snippet(self, raw: str) -> str:
        if not raw:
            return ""
        lines = raw.split("\n")
        matched = [line.strip() for line in lines if "[" in line and "]" in line]
        if not matched:
            return ""
        return " | ".join(matched)

