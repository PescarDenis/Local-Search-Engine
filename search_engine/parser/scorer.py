import time
from pathlib import Path

class FileScorer:
    def __init__(self):
        self.high_priority_dirs = {"src", "docs", "lib", "include", "tests", "examples"}
        self.lwo_priority_dirs = {"build", "node_modules", "tmp", "temp", "cache"}
        self.high_priority_exts = {".py", ".md", ".cpp", ".h", ".c", ".txt", ".json", ".yaml", ".toml", ".rs", ".js", ".ts", ".go"}
        self.low_priority_exts = {".log", ".csv", ".swp", ".bak", ".tmp"}

    def score(self, path: Path, size_bytes: int, modified_at: float) -> float:
        weight = 1.0
        # 1.Path depth
        # Starts at 2 boost for depth 1, 1 for depth 2, and penalizes deeper files
        depth = len(path.parts)
        depth_boost = max(0.2, 2.0 / max(1, depth))
        weight *= depth_boost

        # 2.Directory importance & keyword presence
        parts = set(p.lower() for p in path.parts)
        if parts.intersection(self.high_priority_dirs):
            weight *= 1.3
        if parts.intersection(self.lwo_priority_dirs):
            weight *= 0.6

        # 3.Extension prioritization
        ext = path.suffix.lower()
        if ext in self.high_priority_exts:
            weight *= 1.5
        elif ext in self.low_priority_exts:
            weight *= 0.7

        # 4.Recent file access 
        now = time.time()
        recent_acc = max(0.0, now - modified_at)
        seven_days = 7 * 24 * 3600
        thirty_days = 30 * 24 * 3600
        if recent_acc  < seven_days:
            weight *= 1.2
        elif recent_acc  < thirty_days:
            weight *= 1.05
            
        # 5.File size
        # text files (>2MB)
        two_mb = 2 * 1024 * 1024
        if size_bytes > two_mb:
            weight *= 0.55
            
        return max(0.1, round(weight, 2))
