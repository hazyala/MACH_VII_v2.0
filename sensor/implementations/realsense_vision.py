# sensor/realsense_vision.py

import numpy as np
import logging
from ..core import VisionBase
from ..core import realsense_driver

class RealSenseVision(VisionBase):
    """
    [Layer 1: Sensor Implementation] 실물 Intel RealSense 카메라를 위한 구현체입니다.
    
    VisionBase를 상속받아 실제 하드웨어 드라이버(realsense_driver)로부터 데이터를 획득하고,
    베이스 클래스의 필터링된 좌표 변환 로직을 활용합니다.
    """
    def __init__(self):
        """
        하드웨어를 초기화하고 비전 시스템을 시작합니다.
        """
        super().__init__()
        
        # 1. 하드웨어 드라이버 시작 (싱글톤 활용)
        realsense_driver.start()
        
        # 2. 카메라 내인자(Intrinsics: 렌즈 고유의 초점 거리 및 픽셀 중심점 등 카메라 내부 속성) 설정
        # SDK에서 실제 하드웨어 파라미터를 읽어와 베이스 클래스에 등록합니다.
        intr = realsense_driver.get_intrinsics()
        self.set_intrinsics(fx=intr["fx"], fy=intr["fy"], cx=intr["cx"], cy=intr["cy"])
        
        logging.info(f"[RealSenseVision] 실제 SDK 파라미터 적용 완료: {intr}")

    def get_synced_packet(self):
        """
        RGB, Depth 영상과 해당 시점의 로봇 포즈(Captured Pose)를 하나의 패킷으로 묶어 반환합니다.
        비전-액션 정합(데이터를 시간축에 맞춰 정렬하는 것)을 위해 가장 중요한 메서드입니다.
        """
        color, depth = realsense_driver.get_frames()
        if color is None or depth is None:
            return None
            
        # [Sync] 영상 획득 시점의 로봇 포즈(Joint/Cartesian: 로봇 관절 각도 또는 집게발의 공간 좌표) 연동
        # 실물 로봇의 경우 드라이버로부터 현재 상태를 읽어와야 합니다.
        from state.system_state import system_state
        
        # 현재 system_state에 기록된 가장 최신의 로봇 포즈를 가져옵니다.
        # NOTE: 엄밀하게는 하드웨어 수준에서 타임스탬프 동기화가 필요하지만, 
        # 현재는 비동기적으로 스냅샷을 캡처하는 방식을 사용합니다.
        pose = system_state.robot_status.get("pose", {})
        
        return {
            "color": color,
            "depth": depth,
            "captured_pose": pose
        }

    def pixel_to_cm(self, u: int, v: int, depth_m: float):
        """
        [Override] SDK의 공식 역투영(Deprojection: 2D 이미지를 3D 공간으로 되돌리는 계산) 함수를 사용하여 
        렌즈 왜곡 등이 보정된 최상의 3D 카메라 좌표를 산출합니다.
        """
        if depth_m <= 0:
            return None
            
        # 1. SDK 기반 정밀 역투영 실행
        from sensor.projection import realsense_projection
        raw_intr = realsense_driver.get_raw_intrinsics()
        
        if raw_intr is not None:
             x, y, z = realsense_projection.pixel_to_3d(u, v, depth_m, raw_intr)
        else:
             # SDK 미가용 시 베이스 클래스의 핀홀 모델 사용 (Fallback: 대비책)
             # return super().pixel_to_cm(u, v, depth_m)을 직접 구현
             x = (u - self.cx) * depth_m / self.fx
             y = (v - self.cy) * depth_m / self.fy
             z = depth_m * 100 # m to cm
             
        # 2. [중요] 산출된 좌표에 베이스 클래스의 칼만 필터를 적용하여 떨림 제거
        # 이를 통해 정밀도(SDK)와 안정성(Filter)을 동시에 확보합니다.
        return [
            self.filter_x.update(x),
            self.filter_y.update(y),
            self.filter_z.update(z)
        ]
