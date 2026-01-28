# core/pybullet_vision.py

import numpy as np
from core.vision_base import VisionBase
from interface.backend.pybullet_client import PybulletClient

class PybulletVision(VisionBase):
    def __init__(self):
        super().__init__()
        # 서버와 통신할 전령을 직접 고용합니다.
        self.client = PybulletClient()
        self.client.connect()

    def get_synced_packet(self):
        """서버로부터 영상, 깊이, 포즈를 한 번에 낚아채어 맹칠이에게 바칩니다."""
        return self.client.get_synced_packet()

    def get_frame(self):
        return self.client.get_rgb_frame()

    def get_depth(self):
        return self.client.get_depth_frame()