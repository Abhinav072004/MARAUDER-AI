"""Optional four-point image-to-floor homography (floor units are arbitrary)."""

import cv2
import numpy as np


class FloorMapping:
    def __init__(self, image_points, floor_points):
        source = np.asarray(image_points, dtype=np.float32)
        target = np.asarray(floor_points, dtype=np.float32)
        if source.shape != (4, 2) or target.shape != (4, 2):
            raise ValueError("Floor calibration requires two sets of four 2D points")
        if not np.isfinite(source).all() or not np.isfinite(target).all():
            raise ValueError("Floor calibration must be finite")
        for points in (source, target):
            if abs(cv2.contourArea(cv2.convexHull(points))) < 1e-5:
                raise ValueError("Floor points must span a plane")
        self.matrix = cv2.getPerspectiveTransform(source, target)
        if abs(np.linalg.det(self.matrix)) < 1e-10:
            raise ValueError("Degenerate floor calibration")
        self.inverse = np.linalg.inv(self.matrix)

    def to_floor(self, point):
        return self._transform(point, self.matrix)

    def to_image(self, point):
        return self._transform(point, self.inverse)

    @staticmethod
    def _transform(point, matrix):
        result = matrix @ np.array([*point, 1.0])
        if abs(result[2]) < 1e-8:
            raise ValueError("Point projects to infinity")
        return tuple(result[:2] / result[2])
