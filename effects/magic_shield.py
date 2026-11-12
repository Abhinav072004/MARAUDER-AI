"""Animated energy rings anchored to a pose or a measured cloak bounding box."""

import cv2
import numpy as np


def render_shield(frame, bounds, time):
    if bounds is None:
        return frame
    x, y, w, h = bounds
    center = (round(x + w / 2), round(y + h / 2))
    radius = max(15, round(max(w, h) * 0.6))
    layer = np.zeros_like(frame)
    for index in range(3):
        r = round(radius * (0.85 + 0.06 * index + 0.02 * np.sin(time * 3 + index)))
        cv2.circle(layer, center, r, (190, 85, 35), 1 + index, cv2.LINE_AA)
        angle = (time * 50 + index * 120) % 360
        cv2.ellipse(layer, center, (r, r), 0, angle, angle + 55, (255, 190, 110), 3, cv2.LINE_AA)
    disc = np.zeros_like(frame)
    cv2.circle(disc, center, radius, (60, 25, 15), -1, cv2.LINE_AA)
    return cv2.add(
        cv2.addWeighted(frame, 1, disc, 0.3, 0),
        cv2.add(layer, cv2.GaussianBlur(layer, (15, 15), 0)),
    )
