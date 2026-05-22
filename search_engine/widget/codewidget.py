import os

from collections import Counter
from ..models import SearchContextWidget
from .widget_base import Widget

CODE_EXT = {
    ".py",
    ".js",
    ".ts",
    ".cpp",
    "cpp.o.d",
    "cpp.o",
    ".c",
    ".h",
    ".go",
    ".rs",
    ".java",
}

"""Activates when search results are predominantly source code files."""


class CodeStatsWidget(Widget):

    @property
    def name(self) -> str:
        return "Code Stats"

    def should_activate(self, ctx: SearchContextWidget) -> bool:
        return ctx.code_ratio >= 0.4

    def render(self, ctx: SearchContextWidget) -> str:
        # count how many files did we find of each extension -> aka languages found
        lang_counts: Counter = Counter()
        for r in ctx.results:
            ext = os.path.splitext(r.path)[1].lower()
            if ext in CODE_EXT:
                lang_counts[ext] += 1

        lines = [
            f"   {self.name}",
            f"   Language breakdown count:",
        ]
        for ext, count in lang_counts.most_common():
            lines.append(f"    {ext:6s}  {count} file(s)")
        return "\n".join(lines)
