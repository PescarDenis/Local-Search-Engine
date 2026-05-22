from ..models import SearchContextWidget
from .widget_base import Widget

"""Activates when the query contains a color: qualifier."""


class ColorPaletteWidget(Widget):

    @property
    def name(self) -> str:
        return "Color Palette"

    def should_activate(self, ctx: SearchContextWidget) -> bool:
        return ctx.has_color_query

    def render(self, ctx: SearchContextWidget) -> str:
        # extract unique color names from the preview strings
        colors: set[str] = set()
        for r in ctx.results:
            if r.preview and "Dominant color is:" in r.preview:
                color = r.preview.split("Dominant color is:")[-1].strip()
                if color:
                    colors.add(color)

        lines = [f"   {self.name}"]
        if colors:
            lines.append(f"  Unique colors found: {', '.join(sorted(colors))}")
        else:
            lines.append("  No color metadata available in results")
        return "\n".join(lines)
