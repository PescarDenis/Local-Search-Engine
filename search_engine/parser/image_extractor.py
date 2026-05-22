from pathlib import Path
from collections import Counter
from .base_extractor import BaseExtractor

import cv2
from scipy.cluster.vq import kmeans, vq
import webcolors


# main class that will implement the image extraction and will extract the dominant color
# https://www.w3schools.com/csSref/css_colors.php
# link of references and guidance from whre the code is inspired:
# https://www.geeksforgeeks.org/machine-learning/extract-dominant-colors-of-an-image-using-python/
# https://stackoverflow.com/questions/3241929/how-to-find-the-dominant-most-common-color-in-an-image
# + some ytb videos
class ImageExtractor(BaseExtractor):
    def can_handle(self, mime_type: str) -> bool:
        return mime_type.startswith("image/")

    def extract(self, path: Path) -> dict[str, str]:

        try:
            # read the image with the opencv ->BGR
            img = cv2.imread(str(path))
            if img is None:
                return {"content": "", "preview": "Image file", "color": ""}

            # transpose to RGB
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            # optionally resize the image to speedup the clustering
            img = cv2.resize(img, (50, 50))

            # reshape the image to a list of pixels instead of HxWx3(RGB) we will have
            # a 2D list of pixels
            pixels = img.reshape((-1, 3)).astype(float)

            # perform Kmeans clustering k = 3
            # Kmeans returns a tuple: centroid and distance
            centroids, _ = kmeans(pixels, 3)

            # assign each pixel to a cluster
            # vq returns a tuple: cluster_indices and distances
            # q is an array of indices indicating to which cluster each pixel belongs to
            q, _ = vq(pixels, centroids)

            # count how many pixels we assigned for each cluster
            counts = Counter(q)
            # get the dominant index
            dominant_idx = counts.most_common(1)[0][0]

            c = centroids[dominant_idx]
            # get the RGB values of the dominant centroid
            dominant_rgb = (int(c[0]), int(c[1]), int(c[2]))

            closest_color = self._closest_color(dominant_rgb)

            return {
                "content": "",
                "preview": f"Image file -> Dominant color is: {closest_color}",
                "color": closest_color,
            }
        except Exception:
            return {"content": "", "preview": "Image file", "color": ""}

    """
    Finds the closest readable CSS3 color name for a given RGB tuple.
    It does this by treating RGB values as 3D coordinates and calculating
    the squared Euclidean distance to find the nearest standard color.
    """

    def _closest_color(self, requested_color: tuple[int, int, int]) -> str:
        min_colors = {}
        # loop through every standard CSS3 color name
        for name in webcolors.names("css3"):
            # get the RGB values for this specific CSS3 color
            r_c, g_c, b_c = webcolors.name_to_rgb(name)
            # calculate the euclidian distance
            rd = (r_c - requested_color[0]) ** 2
            gd = (g_c - requested_color[1]) ** 2
            bd = (b_c - requested_color[2]) ** 2
            # save the total distance as the dictionary key and the color name as the value
            min_colors[(rd + gd + bd)] = name
        return min_colors[min(min_colors.keys())]
