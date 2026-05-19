import os

from ..models import SearchContextWidget
from .widget_base import Widget

LOG_EXT = {".log"}

"""Activates when search results are predominantly log files."""

class LogAnalyzerWidget(Widget):
    @property
    def name(self) -> str:
        return "Analyze Logs"

    def should_activate(self, ctx: SearchContextWidget) -> bool:
        # ctivate if >=40% of results are .log files
        if ctx.log_ratio >= 0.4:
            return True
        #or if the query mentions 'log' and there is at least one .log file
        if "log" in ctx.raw_query.lower().split() and ctx.log_ratio > 0:
            return True
        return False

    def render(self, ctx: SearchContextWidget) -> str:
        log_count = sum(ctx.extension_counts[e] for e in LOG_EXT)
        log_files = [r for r in ctx.results if os.path.splitext(r.path)[1].lower() in LOG_EXT]
        lines = [
            f"   {self.name}",
            f"   {log_count} log file(s) found in results",
        ]
        #show the most recently modified log file
        if log_files:
            newest = max(log_files, key=lambda r: r.modified_at)
            lines.append(f"    Most recent: {newest.filename}")
        return "\n".join(lines)

