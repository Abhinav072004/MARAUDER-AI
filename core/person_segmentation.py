"""Optional small MediaPipe person mask; HSV always remains the primary key."""

import cv2
import numpy as np


class PersonSegmentation:
    def __init__(self):
        import mediapipe as mp

        self.last_mask = None
        self.model = mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=1)

    def refine(self, frame, cloak_mask):
        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(cv2.resize(frame, (256, round(h * 256 / w))), cv2.COLOR_BGR2RGB)
        result = self.model.process(rgb)
        probability = cv2.resize(result.segmentation_mask, (w, h))
        self.last_mask = np.rint(np.clip(probability, 0, 1) * 255).astype(np.uint8)
        # Conservative gate. Never turn non-cloth pixels into invisible pixels.
        confidence = np.clip((probability - 0.1) / 0.3, 0, 1)
        return np.rint(cloak_mask * confidence).astype(np.uint8)

    def close(self):
        self.model.close()
