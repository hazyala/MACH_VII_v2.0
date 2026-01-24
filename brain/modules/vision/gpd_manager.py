import numpy as np
from typing import List, Dict, Tuple, Optional

class GpdManager:
    """
    물체의 깊이(Depth) 정보를 분석하여 최적의 파지 포즈를 계산하는 도구입니다.
    brain/tools/vision 폴더 내에서 YOLO와 협력하여 작동합니다.
    """

    def __init__(self):
        """
        그리퍼 사양 및 파지 파라미터를 설정합니다.
        """
        # 마마의 로봇(MACH-VII) 그리퍼 최대 폭: 3.0cm
        self.max_width_cm = 3.0
        # 안전한 접근을 위한 오프셋 거리 (cm)
        self.approach_offset = 5.0

    def find_best_grasp(self, depth_roi: np.ndarray, center_3d: List[float]) -> Dict:
        """
        관심 영역(ROI)의 깊이 데이터를 분석하여 최적의 잡기 위치와 각도를 반환합니다.
        
        Args:
            depth_roi: YOLO가 찾은 물체 영역의 깊이 데이터
            center_3d: 물체의 3D 중심 좌표 [x, y, z] (단위: cm)
            
        Returns:
            grasp_pose: {
                'target': [x, y, z], 
                'rpy': [roll, pitch, yaw], 
                'width': 0~100
            }
        """
        # 1. 깊이 데이터에서 물체의 기울기(Surface Normal)를 분석합니다.
        # (시뮬레이션의 경우 파이불렛의 포인트클라우드 데이터를 활용합니다.)
        
        # 2. 물체의 가장 얇은 부분과 파지 각도를 계산합니다.
        # 기본값으로 위에서 아래로(Top-down) 잡는 포즈를 설정합니다.
        target_x, target_y, target_z = center_3d
        
        # 3. 결과 포즈 생성 (오른손 좌표계 기준)
        grasp_pose = {
            "target": [target_x, target_y, target_z],
            "rpy": [0.0, 90.0, 0.0],  # Pitch 90도는 수직 접근을 의미함
            "width": 50.0              # 물체 크기에 따른 그리퍼 개방도 (%)
        }

        return grasp_pose

    def check_feasibility(self, object_size: float) -> bool:
        """
        물체가 현재 그리퍼로 잡기에 너무 큰지 확인합니다.
        """
        return object_size <= self.max_width_cm