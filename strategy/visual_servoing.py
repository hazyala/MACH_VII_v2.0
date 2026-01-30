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
                      max_iterations: int = 100,
                      tolerance_cm: float = 1.0) -> bool:
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
        
        # 1. 초기 속도/힘 설정 (확실한 이동을 위해)
        # 클라이언트 객체에 직접 접근하지 않고 기본 설정에 의존하거나, 
        # 필요하다면 별도 메서드로 설정해야 함. 여기서는 로직 개선에 집중.

        for iteration in range(max_iterations):
            current_ee = get_ee_position()
            distance = self.compute_distance(current_ee, target_position)
            
            # 1. 최종 목표 도달 확인
            if distance < tolerance_cm:
                logging.info(f"[VisualServoing] ✅ 목표 도달 성공 (오차: {distance:.2f}cm, 시도: {iteration}회)")
                return True
                
            # 2. 보폭 결정 (30회 이내 목표 달성을 위해 대담한 보폭)
            if distance > 10.0:
                step_size = 10.0 # 10cm씩 이동
                speed = self.normal_speed
                sub_tolerance = 2.0 # 중간 목표 대기 허용오차
            elif distance > 5.0:
                step_size = 5.0
                speed = self.normal_speed
                sub_tolerance = 1.0
            else:
                step_size = 0.5 # 2cm 미만: 0.5cm씩 세밀하게
                speed = self.precision_speed
                sub_tolerance = 0.2

            # 3. 다음 중간 목표(Sub-target) 계산
            next_position = self.get_next_linear_step(current_ee, target_position, step_size, distance)
            
            logging.info(f"[VisualServoing] 스텝 {iteration+1} - 거리: {distance:.1f}cm → 이동: {step_size:.1f}cm")
            
            # 4. 로봇 이동 명령
            if not move_robot(next_position, speed):
                logging.error("[VisualServoing] 로봇 이동 실패")
                return False
            
            # 5. [핵심] 이동 완료 대기 (Wait-to-Reach)
            # 물리적 이동 시간을 부여하여 명령 횟수를 줄임
            wait_start = time.time()
            max_wait = 3.0 # 최대 3초 대기
            
            while time.time() - wait_start < max_wait:
                curr = get_ee_position()
                dist_to_sub = self.compute_distance(curr, next_position)
                
                # 중간 목표 도달 확인
                if dist_to_sub < sub_tolerance:
                    break
                
                # 움직임이 멈췄는지 확인 (선택 사항)
                
                time.sleep(0.1) # 10Hz 체크
            
            # 대기 후 상태 확인 (디버깅용)
            post_ee = get_ee_position()
            moved_dist = self.compute_distance(current_ee, post_ee)
            # logging.debug(f"  ↳ 실제 이동 거리: {moved_dist:.2f}cm")
            
        logging.warning(f"[VisualServoing] 최대 반복 횟수 도달 (남은거리: {distance:.2f}cm)")
        return distance < tolerance_cm


# 싱글톤 인스턴스
visual_servoing = VisualServoing()
