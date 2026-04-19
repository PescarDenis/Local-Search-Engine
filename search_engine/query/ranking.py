from abc import ABC, abstractmethod

class RankingStrategy(ABC):
    #Base Strategy Interface for generating SQL ORDER BY sorting clauses
    #and optionally refining those results in python memory.
    @abstractmethod
    def get_order_by(self) -> str:
        #Returns the ORDER BY clause directly injected into the SQL query
        pass

    def apply_ranking(self, results: list) -> list:
        #Sort results further in memory
        return results

class RelevanceRanking(RankingStrategy):
    def get_order_by(self) -> str:
        return "combined_score ASC"

class AlphabeticalRanking(RankingStrategy):
    def get_order_by(self) -> str:
        return "f.filename ASC"

class DateRanking(RankingStrategy):
    def get_order_by(self) -> str:
        return "f.modified_at DESC"

class HistoryRanking(RankingStrategy):
    def __init__(self, tracker):
        self.tracker = tracker

    def get_order_by(self) -> str:
        #Base ordering is relevance, we refine it next
        return "combined_score ASC"
        
    def apply_ranking(self, results: list) -> list:
        #Dynamically adjusts the ranking score of results that match historically popular searches
        top_queries = self.tracker.get_top_queries(5)
        if not top_queries:
            return results
            
        for r in results:
            filename_lower = r.filename.lower()
            for q in top_queries:
                if q in filename_lower:
                    # boost the score via subtraction
                    r.score -= 5.0
                    
        def _get_score(item):
            return item.score
            
        #Resort based on the new modified scores
        return sorted(results, key=_get_score)
