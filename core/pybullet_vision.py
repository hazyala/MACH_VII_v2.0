# core/pybullet_vision.py

from core.vision_base import VisionBase
from interface.backend.pybullet_client import PybulletClient
import numpy as np

class PybulletVision(VisionBase):
    """
    파이불렛 시뮬레이션 환경에서 영상을 획득하고 좌표를 계산하는 클래스입니다.
    """
    def __init__(self):
        super().__init__()
        # 파이불렛 서버와 통신하는 클라이언트를 초기화합니다.
        self.client = PybulletClient()
        self.client.connect()
        
        # 카메라 내인자(Intrinsics) 설정: 640x480 해상도 기준 기본값
        # fx, fy: 초점 거리, cx, cy: 주점(중심점) 좌표
        self.set_intrinsics(fx=554.25, fy=554.25, cx=320.0, cy=240.0)

    def get_frame(self):
        """
        최신 RGB 영상과 Depth 데이터를 획득하여 딕셔너리 형태로 반환합니다.
        """
        color = self.client.get_rgb_frame()
        depth = self.client.get_depth_frame()
        
        if color is None or depth is None:
            return None
            
        return {
            "color": color,
            "depth": depth
        }