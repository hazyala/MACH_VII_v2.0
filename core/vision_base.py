from abc import ABC, abstractmethod
from typing import List, Optional
from shared.filters import KalmanFilter

class VisionBase(ABC):
    """
    비전 시스템의 공통 인터페이스입니다.
    2D 픽셀 좌표와 깊이(Depth) 정보를 3D 좌표로 변환하는 규격을 정의합니다.
    """

    def __init__(self):
        """
        카메라 내인자(Intrinsics)와 3D 좌표 정제용 필터를 초기화합니다.
        """
        # 카메라 내부 파라미터 (Subclass에서 실제 값으로 갱신 필요)
        self.fx, self.fy = 0.0, 0.0
        self.cx, self.cy = 0.0, 0.0
        
        # 3D 공간 좌표(x, y, z) 떨림 방지를 위한 칼만 필터
        self.filter_x = KalmanFilter()
        self.filter_y = KalmanFilter()
        self.filter_z = KalmanFilter()

    def set_intrinsics(self, fx: float, fy: float, cx: float, cy: float):
        """
        카메라의 내인자 값을 설정합니다.
        """
        self.fx, self.fy = fx, fy
        self.cx, self.cy = cx, cy

    def pixel_to_cm(self, u: float, v: float, depth_m: float) -> Optional[List[float]]:
        """
        핀홀 카메라 모델을 사용하여 2D 픽셀을 3D cm 좌표로 변환합니다.
        파이불렛 서버의 미터(m) 단위를 센티미터(cm)로 변환하여 계산합니다.
        """
        if depth_m <= 0:
            return None

        # 미터 단위를 센티미터로 변환 (1m = 100cm)
        z_cm = depth_m * 100.0
        
        # 핀홀 카메라 역투영 공식 적용
        x_cm = (u - self.cx) * z_cm / self.fx
        y_cm = (v - self.cy) * z_cm / self.fy

        # 3D 좌표에 칼만 필터 적용
        filtered_x = self.filter_x.update(x_cm)
        filtered_y = self.filter_y.update(y_cm)
        filtered_z = self.filter_z.update(z_cm)

        return [filtered_x, filtered_y, filtered_z]

    @abstractmethod
    def get_frame(self):
        """실제 영상 및 깊이 데이터를 획득하는 추상 메서드입니다."""
        pass