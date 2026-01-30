# strategy/visual_servoing.py

import logging
import time
from typing import Dict, Callable
import numpy as np

class VisualServoing:
    """
    비주얼 서보잉 제어 클래스
    실시간 직선 보간을 통해 목표물에 정밀하게 접근합니다.
    """
    
    def __init__(self, precision_threshold_cm: float = 3.0):
        self.precision_threshold = precision_threshold_cm
        self.normal_speed = 50
        self.precision_speed = 10
        
    def compute_distance(self, pos1: Dict[str, float], pos2: Dict[str, float]) -> float:
        """두 3D 좌표 간의 유클리드 거리 계산 (cm)"""
        dx = pos1["x"] - pos2["x"]
        dy = pos1["y"] - pos2["y"]
        dz = pos1["z"] - pos2["z"]
        return np.sqrt(dx**2 + dy**2 + dz**2)
    
    def get_next_linear_step(self, current: Dict[str, float], target: Dict[str, float], 
                             step_size: float, distance: float) -> Dict[str, float]:
        """
        현재 위치에서 목표 위치 방향으로 직선 보간된 다음 지점을 계산합니다.
        
        Args:
            current: 현재 위치 {x, y, z}
            target: 목표 위치 {x, y, z}
            step_size: 이동할 거리 (cm)
            distance: 현재-목표 간 전체 거리 (cm)
            
        Returns:
            next_position: 다음 이동 목표 좌표
        """
        if distance <= 0:
            return current.copy()
            
        # 전체 거리 중 현재 보폭의 비율(t) 계산
        t = step_size / distance
        
        return {
            "x": current["x"] + t * (target["x"] - current["x"]),
            "y": current["y"] + t * (target["y"] - current["y"]),
            "z": current["z"] + t * (target["z"] - current["z"])
        }

    def servoing_loop(self,
                      target_position: Dict[str, float],
                      get_ee_position: Callable[[], Dict[str, float]],
                      move_robot: Callable[[Dict[str, float], int], bool],
                      max_iterations: int = 300,
                      tolerance_cm: float = 0.5) -> bool:
        """
        비주얼 서보잉 피드백 제어 메인 루프
        
        Args:
            target_position: 목표 위치 {x, y, z} (cm)
            get_ee_position: 현재 엔드이펙터 위치를 반환하는 함수
            move_robot: 로봇을 이동시키는 함수 (position, speed)
            max_iterations: 최대 반복 횟수
            tolerance_cm: 목표 도달 판정 허용 오차 (cm)
            
        Returns:
            success: 목표 도달 성공 여부
        """
        logging.info(f"[VisualServoing] 제어 시작 - Target: {target_position}")
        
        # V1.0 스타일: 정체 감지 없는 깔끔한 루프
        for iteration in range(max_iterations):
            current_ee = get_ee_position()
            distance = self.compute_distance(current_ee, target_position)
            
            # 1. 도달 확인 (0.5cm 이내)
            if distance < tolerance_cm:
                logging.info(f"[VisualServoing] ✅ 목표 도달 성공 (오차: {distance:.2f}cm)")
                return True
                
            # 2. V1.0 방식: 간단한 보폭 결정 (10cm 기준)
            if distance > 10.0:
                step_size = 5.0  # 10cm 이상: 5cm씩 이동
                speed = self.normal_speed
            else:
                step_size = 1.0  # 10cm 이하: 1cm씩 정밀 이동
                speed = self.precision_speed

            # 3. 직선 보간을 통한 다음 위치 계산
            next_position = self.get_next_linear_step(current_ee, target_position, step_size, distance)
            
            logging.debug(f"[VisualServoing] 반복 {iteration+1}/{max_iterations} - "
                        f"거리: {distance:.2f}cm, 스텝: {step_size:.2f}cm")
            
            # 4. 로봇 이동
            if not move_robot(next_position, speed):
                logging.error("[VisualServoing] 로봇 이동 실패")
                return False
            
            # 5. 시뮬레이션 스텝 대기 (50ms)
            time.sleep(0.05)
            
        # 최대 반복 도달 시 거리 확인
        logging.warning(f"[VisualServoing] 최대 반복 횟수 도달 (목표거리: {distance:.2f}cm)")
        return distance < 2.0


# 싱글톤 인스턴스
visual_servoing = VisualServoing()
