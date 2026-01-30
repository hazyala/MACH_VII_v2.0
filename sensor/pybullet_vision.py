# sensor/pybullet_vision.py

import numpy as np
import logging
from sensor.vision_base import VisionBase
from interface.sim_client import pybullet_client
from sensor.projection import pybullet_projection

class PybulletVision(VisionBase):
    def __init__(self):
        super().__init__()
        # 이미 생성된 싱글톤 인스턴스를 사용합니다.
        self.client = pybullet_client
        self.client.connect()
        
        logging.info("[PybulletVision] PyBullet projection 모듈 사용 (view/proj matrix 기반)")
        
    def pixel_to_cm(self, u: int, v: int, depth_val: float):
        """
        픽셀 좌표를 3D 월드 좌표(cm)로 변환합니다.
        pybullet_projection 모듈의 정확한 역투영 사용.
        
        Args:
            u, v: 픽셀 좌표
            depth_val: Z-buffer 값 (0~1)
        
        Returns:
            [x, y, z]: 월드 좌표 cm 리스트 (칼만 필터 적용 후)
        """
        if depth_val <= 0:
            return None
        
        # PyBullet projection 모듈 사용
        x_cm, y_cm, z_cm = pybullet_projection.pixel_to_3d(u, v, depth_val)
        
        # 칼만 필터 적용
        filtered_x = self.filter_x.update(x_cm)
        filtered_y = self.filter_y.update(y_cm)
        filtered_z = self.filter_z.update(z_cm)
        
        logging.info(f"[PybulletVision.pixel_to_cm] "
                    f"픽셀=({u}, {v}), depth={depth_val:.4f} → "
                    f"월드=({x_cm:.2f}, {y_cm:.2f}, {z_cm:.2f})cm → "
                    f"필터=({filtered_x:.2f}, {filtered_y:.2f}, {filtered_z:.2f})cm")
        
        return [filtered_x, filtered_y, filtered_z]

    def get_synced_packet(self):
        """서버로부터 영상, 깊이, 포즈를 한 번에 낚아채어 맹칠이에게 바칩니다."""
        packet = self.client.get_synced_packet()
        if not packet:
            logging.warning("[PybulletVision] 동기화 패킷 수신 실패")
        return packet

    def get_frame(self):
        return self.client.get_rgb_frame()

    def get_depth(self):
        return self.client.get_depth_frame()