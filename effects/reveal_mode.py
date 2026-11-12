"""Pulsing coloured cloak silhouette and glowing boundary."""
import cv2
import numpy as np


def render_reveal(frame, mask, time, heatmap=False):
    alpha = mask.astype(np.float32)[..., None] / 255 * 0.35
    if heatmap:
        color = cv2.applyColorMap(mask, cv2.COLORMAP_TURBO)
    else:
        color = np.full_like(frame, (180, 70, 220))
    output = (frame * (1 - alpha) + color * alpha).astype(np.uint8)
    edges = cv2.morphologyEx(mask, cv2.MORPH_GRADIENT, np.ones((5, 5), np.uint8))
    glow = cv2.GaussianBlur(edges, (9, 9), 0).astype(np.float32) / 255
    return np.clip(output + glow[..., None] * np.array([255, 130, 240]) *
                   (0.5 + 0.25 * np.sin(time * 4)), 0, 255).astype(np.uint8)
