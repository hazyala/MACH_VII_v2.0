# strategy/grasp_planner.py

import numpy as np
import logging
from typing import Dict, List, Optional, Tuple

class GraspPlanner:
    """
    GPD (Grasp Pose Detection) - 물체의 그립 자세를 계산하는 클래스
    
    클라우드 포인트 기반 그립 자세 생성 (규칙 기반 + 메모리 기반 하이브리드)
    """
    
    def __init__(self):
        # 물체별 최적 그립 오프셋 메모리 (학습 가능)
        self.grasp_memory = {
            "bottle": {"approach_offset_z": 5.0, "gripper_width": 50.0},
            "cup": {"approach_offset_z": 5.0, "gripper_width": 60.0},
            "teddy": {"approach_offset_z": 8.0, "gripper_width": 80.0},
            "duck": {"approach_offset_z": 5.0, "gripper_width": 50.0},
            "soccerball": {"approach_offset_z": 10.0, "gripper_width": 100.0},
            "default": {"approach_offset_z": 5.0, "gripper_width": 60.0}
        }
    
    def compute_grasp_pose(self, 
                          object_name: str, 
                          object_position: Dict[str, float],
                          depth_map: Optional[np.ndarray] = None) -> Dict[str, any]:
        """
        물체의 그립 자세를 계산합니다.
        
        Args:
            object_name: 물체 이름
            object_position: 물체 중심 좌표 {x, y, z} (cm)
            depth_map: 깊이 맵 (선택적, 더 정밀한 그립 계산용)
            
        Returns:
            grasp_pose: {
                "pre_grasp": {x, y, z},  # 접근 위치
                "grasp": {x, y, z},       # 잡기 위치
                "gripper_width": float     # 그리퍼 개방 정도 (%)
            }
        """
        # 1. 메모리에서 물체별 그립 파라미터 가져오기
        params = self.grasp_memory.get(object_name, self.grasp_memory["default"])
        
        # 2. 규칙 기반: 수직 하강 그립 계산 (Top-Down Grasp)
        # 접근 위치: 물체 위쪽에서 접근
        pre_grasp_pos = {
            "x": object_position["x"],
            "y": object_position["y"],
            "z": object_position["z"] + params["approach_offset_z"]
        }
        
        # 잡기 위치: 물체 중심
        grasp_pos = {
            "x": object_position["x"],
            "y": object_position["y"],
            "z": object_position["z"]
        }
        
        # 3. 클라우드 포인트 기반 보정 (depth_map이 있는 경우)
        if depth_map is not None:
            # TODO: 깊이 맵으로부터 물체 표면 법선 벡터 계산
            # TODO: 최적 그립 방향 결정
            pass
        
        # 4. 그리퍼 개방 정도 계산 (0~100%)
        gripper_open_percent = min(params["gripper_width"], 100.0)
        
        grasp_pose = {
            "pre_grasp": pre_grasp_pos,
            "grasp": grasp_pos,
            "gripper_width": gripper_open_percent,
            "object_name": object_name
        }
        
        logging.info(f"[GraspPlanner] {object_name} 그립 자세 계산 완료: "
                    f"접근={pre_grasp_pos}, 잡기={grasp_pos}, 그리퍼={gripper_open_percent}%")
        
        return grasp_pose
    
    def update_grasp_memory(self, object_name: str, success: bool, params: Dict):
        """
        그립 성공/실패에 따라 메모리를 업데이트합니다 (학습)
        
        Args:
            object_name: 물체 이름
            success: 그립 성공 여부
            params: 사용한 그립 파라미터
        """
        if success:
            logging.info(f"[GraspPlanner] {object_name} 그립 성공! 파라미터 저장.")
            self.grasp_memory[object_name] = params
        else:
            logging.warning(f"[GraspPlanner] {object_name} 그립 실패. 파라미터 조정 필요.")
            # TODO: 실패 시 파라미터 자동 조정 로직


# 싱글톤 인스턴스
grasp_planner = GraspPlanner()
