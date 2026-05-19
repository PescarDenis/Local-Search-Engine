import os
from ..models import SearchContextWidget
from .widget_base import Widget

#This list is arbitrary as the current search engine, will actually search for content, or file names
#it can be useful when you have a strict dir "images" for ex and search in it -> this way makes sense
IMAGE_QUERY_KEYWORDS = {"image", "images", "photo", "photos", "picture", "pictures", "gallery"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"}

"""Activates when search results are predominantly image files."""

class GalleryWidget(Widget):
    @property
    def name(self) -> str:
        return "View as Gallery"

    def should_activate(self, ctx: SearchContextWidget) -> bool:
        #activate if >=40% of results are images
        if ctx.image_ratio >= 0.4:
            return True
        #or if the query mentions image related keywords and there is at least one image
        query_words = set(ctx.raw_query.lower().split())
        if query_words & IMAGE_QUERY_KEYWORDS and ctx.image_ratio > 0:
            return True
        return False

    def render(self, ctx: SearchContextWidget) -> str:
        image_count = sum(ctx.extension_counts[e] for e in IMAGE_EXT)
        image_files = [r.filename for r in ctx.results if os.path.splitext(r.path)[1].lower() in IMAGE_EXT]
        lines = [
            f"    {self.name}",
            f"    {image_count} image file(s) found in results",
        ]
        #print the first 5 images found
        for fname in image_files[:5]:
            lines.append(f"    • {fname}")
        #if there are more just print some dots
        if len(image_files) > 5:
            lines.append(f"    ... and {len(image_files) - 5} more")
        return "\n".join(lines)
