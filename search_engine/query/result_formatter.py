from ..models import SearchResult

class ResultFormatter:
    def format(self, rows: list) -> list[SearchResult]:
        results = []
        for row in rows:
            try:
                results.append(
                    SearchResult(
                        path=row["path"],
                        filename=row["filename"],
                        preview=row["snippet"] or row["preview"] or "",
                        modified_at=row["modified_at"],
                        score=row["rank"],
                    )
                )
            except (IndexError, KeyError, TypeError):
                continue
        return results
