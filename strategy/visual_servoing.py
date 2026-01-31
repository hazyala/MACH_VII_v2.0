# strategy/visual_servoing.py

import logging
import time
import threading
import math
from typing import Dict, Callable, Optional
from enum import Enum, auto

from state.system_state import system_state
from shared.state_broadcaster import broadcaster

class ServoState(Enum):
    """비주얼 서보잉 상태"""
    IDLE = auto()
    DETECT = auto()
    VISUAL_SERVO = auto()  # 연속 제어 루프
    GRASP = auto()
    LIFT = auto()
    VERIFY = auto()
    SUCCESS = auto()
    FAIL = auto()

class VisualServoing:
    """
    연속 제어 기반 비주얼 서보잉
    
    핵심 아이디어:
    - 20Hz 피드백 루프로 실시간 위치 보정
    - 비례 제어 (P-Control)로 오차를 점진적으로 감소
    - PyBullet에서 실시간 수신하는 엔드이펙터 좌표 활용
    - 서버 ACK 불필요 (매 루프에서 현재 위치 확인)
    """
    
    def __init__(self):
        self.lock = threading.Lock()
        self.current_state = ServoState.IDLE
        self.cancel_token = threading.Event()
        self.is_running = False
        
        # 제어 파라미터 (정밀도 우선)
        self.LOOP_HZ = 10           # 루프 주파수 (Hz) - 안정성 우선
        self.GAIN = 0.8             # 비례 제어 게인 (80%씩 보정) - 안정적 이동
        self.XY_THRESHOLD = 1.0     # XY 정렬 판정 (cm) - 정밀 제어
        self.Z_THRESHOLD = 0.5      # Z 도달 판정 (cm) - 정밀 제어
        self.APPROACH_HEIGHT = 8.0  # 접근 높이 오프셋 (cm) - 여유 있게 진입
        self.GRASP_DEPTH = 0.0      # 파지 깊이 오프셋 (cm) - Vision이 정확한 중심을 주므로 오프셋 0
    
    def stop(self):
        """외부에서 호출 가능한 긴급 정지"""
        logging.warning("[VisualServoing] 🛑 긴급 정지 요청!")
        self.cancel_token.set()
    
    def find_target_object(self, target_label: str) -> Optional[Dict]:
        """시스템 상태에서 목표 물체 탐지"""
        objects = system_state.perception_data.get("detected_objects", [])
        candidates = [obj for obj in objects 
                     if target_label.lower() in obj["name"].lower()]
        return candidates[0] if candidates else None
    
    def execute_pick_sequence(self,
                             target_label: str,
                             get_ee_position: Callable[[], Dict[str, float]],
                             move_robot: Callable[[float, float, float, int, bool, float], bool],  # wait_arrival, timeout 추가
                             move_gripper: Callable[[float], bool],
                             get_gripper_ratio: Optional[Callable[[], float]] = None,
                             grasp_offset_z: float = -1.5) -> bool:
        """
        비주얼 서보잉 메인 시퀀스
        
        Args:
            target_label: 목표 물체 이름
            get_ee_position: 엔드이펙터 위치 조회 함수
            move_robot: 로봇 이동 명령 함수
            move_gripper: 그리퍼 제어 함수
            get_gripper_ratio: 그리퍼 상태 조회 (사용 안 함)
            grasp_offset_z: 파지 깊이 오프셋
        
        Returns:
            성공 여부
        """
        with self.lock:
            if self.is_running:
                logging.warning("[VisualServoing] 이미 실행 중")
                return False
            self.is_running = True
            self.cancel_token.clear()
            self.current_state = ServoState.IDLE
        
        logging.info(f"[VisualServoing] '{target_label}' 파지 시퀀스 시작")
        broadcaster.publish("agent_thought", 
                          f"[VisualServoing] '{target_label}' 파지 시작")
        
        success = False
        self.GRASP_DEPTH = grasp_offset_z
        
        try:
            # State Machine Loop
            while not self.cancel_token.is_set():
                
                if self.current_state == ServoState.IDLE:
                    self._transition(ServoState.DETECT)
                
                elif self.current_state == ServoState.DETECT:
                    target = self.find_target_object(target_label)
                    if target:
                        logging.info(f"[DETECT] 물체 발견: {target['name']} at {target['position']}")
                        broadcaster.publish("agent_thought", 
                                          f"[VisualServoing] '{target['name']}' 발견")
                        self._transition(ServoState.VISUAL_SERVO)
                    else:
                        logging.warning(f"[DETECT] '{target_label}' 미발견, 재시도...")
                        if self.cancel_token.wait(1.0): break
                        # 3초 동안 3회 재시도
                        retry_count = getattr(self, '_detect_retry', 0)
                        if retry_count >= 3:
                            logging.error(f"[DETECT] '{target_label}' 탐지 실패 (3회)")
                            self._transition(ServoState.FAIL)
                        else:
                            self._detect_retry = retry_count + 1
                
                elif self.current_state == ServoState.VISUAL_SERVO:
                    # 연속 제어 피드백 루프
                    if self._visual_servo_loop(target_label, get_ee_position, move_robot):
                        logging.info("[VisualServo] 목표 위치 도달 완료!")
                        broadcaster.publish("agent_thought", 
                                          "[VisualServoing] 목표 위치 도달")
                        self._transition(ServoState.GRASP)
                    else:
                        self._transition(ServoState.FAIL)
                
                elif self.current_state == ServoState.GRASP:
                    logging.info("[GRASP] 그리퍼 닫기")
                    broadcaster.publish("agent_thought", 
                                      "[VisualServoing] 그리퍼로 파지 중...")
                    
                    # 그리퍼 닫기 명령 전송
                    move_gripper(0)
                    logging.info("[GRASP] 그리퍼 닫는 중... (3.5초 대기)")
                    
                    # PyBullet은 그리퍼 상태 피드백이 없음
                    # 충분한 대기 시간으로 완전 닫힘 보장: 3.5초
                    if self.cancel_token.wait(3.5):
                        logging.warning("[GRASP] 취소됨")
                        break
                    
                    logging.info("[GRASP] ✅ 그리퍼 완전히 닫힘 (3.5초 대기 완료)")
                    self._transition(ServoState.LIFT)
                
                elif self.current_state == ServoState.LIFT:
                    logging.info("[LIFT] 들어올리기")
                    broadcaster.publish("agent_thought", 
                                      "[VisualServoing] 물체 들어올리는 중...")
                    
                    current = get_ee_position()
                    lift_target = {
                        'x': current['x'],
                        'y': current['y'],
                        'z': current['z'] + 15.0  # 15cm 상승
                    }
                    
                    # **동기 모드**: 완전히 들어올릴 때까지 대기 (10초 타임아웃)
                    success = move_robot(lift_target['x'], lift_target['y'], 
                                        lift_target['z'], speed=40, wait_arrival=True, timeout=10.0)
                    
                    if not success:
                        logging.error("[LIFT] 들어올리기 실패 (타임아웃)")
                        self._transition(ServoState.FAIL)
                    else:
                        logging.info("[LIFT] 들어올리기 완료")
                        self._transition(ServoState.VERIFY)
                
                
                elif self.current_state == ServoState.VERIFY:
                    # VLM 검증은 Agent가 직접 수행
                    # 여기서는 즉시 SUCCESS로 전환
                    logging.info("[VERIFY] Visual Servoing 완료, Agent가 VLM 검증 수행 예정")
                    broadcaster.publish("agent_thought", 
                                      "[VisualServoing] 파지 시퀀스 완료! Agent가 검증하겠습니다...")
                    self._transition(ServoState.SUCCESS)
                
                elif self.current_state == ServoState.SUCCESS:
                    broadcaster.publish("agent_thought", 
                                      f"[VisualServoing] '{target_label}' 파지 성공! ✅")
                    break
                
                elif self.current_state == ServoState.FAIL:
                    broadcaster.publish("agent_thought", 
                                      "[VisualServoing] 파지 실패 ❌")
                    break
                
                time.sleep(0.01)  # State Machine 루프 주기
        
        except Exception as e:
            logging.error(f"[VisualServoing] 예외 발생: {e}")
            import traceback
            logging.error(traceback.format_exc())
            success = False
        
        finally:
            self.is_running = False
            if self.cancel_token.is_set():
                logging.warning("[VisualServoing] 작업이 취소되었습니다")
                broadcaster.publish("agent_thought", 
                                  "[VisualServoing] 작업 취소됨")
                success = False
        
        return success
    
    def _visual_servo_loop(self,
                          target_label: str,
                          get_ee_position: Callable[[], Dict[str, float]],
                          move_robot: Callable[[float, float, float, int], bool]) -> bool:
        """
        연속 제어 피드백 루프
        
        Phase 1 (APPROACH): XY 정렬 (Z는 물체 위 5cm 유지)
        Phase 2 (DESCEND): Z축 하강 (XY 고정)
        
        Returns:
            성공 여부
        """
        phase = "APPROACH"
        timeout = 60.0  # 타임아웃 60초
        start_time = time.time()
        
        logging.info("[VisualServo] 연속 제어 루프 시작 (20Hz)")
        
        while not self.cancel_token.is_set():
            loop_start = time.time()
            
            # 타임아웃 체크
            if time.time() - start_time > timeout:
                logging.warning(f"[VisualServo] 타임아웃 (30초 경과)")
                return False
            
            # 1. 현재 상태 획득
            current_ee = get_ee_position()
            target_obj = self.find_target_object(target_label)
            
            if not target_obj:
                # [개선] 무한 대기 방지
                retry_tracker = getattr(self, '_loop_retry_start', None)
                if retry_tracker is None:
                    self._loop_retry_start = time.time()
                    retry_tracker = time.time()
                
                elapsed_retry = time.time() - retry_tracker
                if elapsed_retry > 2.0:  # 2초간 못 찾으면 실패
                    logging.error("[VisualServo] 물체 소실 타임아웃 (2초)")
                    return False
                
                logging.warning(f"[VisualServo] 물체 소실, 재탐지 대기... ({elapsed_retry:.1f}s)")
                time.sleep(0.1)
                continue
            else:
                self._loop_retry_start = None  # 찾으면 리셋
            
            target_pos = target_obj['position']
            
            # 2. Phase별 목표 위치 설정
            if phase == "APPROACH":
                # Phase 1: XY 정렬 (물체 바로 위)
                goal = {
                    'x': target_pos['x'],
                    'y': target_pos['y'],
                    'z': target_pos['z'] + self.APPROACH_HEIGHT
                }
                
                # XY 오차 계산
                xy_error = math.sqrt(
                    (current_ee['x'] - goal['x'])**2 +
                    (current_ee['y'] - goal['y'])**2
                )
                
                # XY 정렬 완료 판정
                if xy_error < self.XY_THRESHOLD:
                    phase = "DESCEND"
                    logging.info(f"[VisualServo] ✅ XY 정렬 완료 (오차: {xy_error:.2f}cm)")
                    logging.info(f"[VisualServo] Phase 전환: APPROACH → DESCEND")
            
            elif phase == "DESCEND":
                # Phase 2: Z축 하강 (XY 고정)
                goal = {
                    'x': target_pos['x'],
                    'y': target_pos['y'],
                    'z': target_pos['z'] + self.GRASP_DEPTH
                }
                
                # Z 오차 계산
                z_error = abs(current_ee['z'] - goal['z'])
                
                # Z 도달 판정 (매우 엄격: 1.0cm 이내)
                if z_error < self.Z_THRESHOLD:
                    logging.info(f"[VisualServo] ✅ 목표 정밀 도달! (Z 오차: {z_error:.2f}cm)")
                    # 추가 안정화: 0.3초 대기 후 그리퍼 단계로
                    time.sleep(0.3)
                    return True  # 성공
                elif z_error > 3.0:
                    logging.warning(f"[VisualServo] ⚠️ Z 오차 과다: {z_error:.2f}cm (계속 접근 중...)")
            
            # 3. 오차 계산
            error_x = goal['x'] - current_ee['x']
            error_y = goal['y'] - current_ee['y']
            error_z = goal['z'] - current_ee['z']
            
            total_error = math.sqrt(error_x**2 + error_y**2 + error_z**2)
            
            # 4. 비례 제어 (P-Control)
            cmd_x = current_ee['x'] + error_x * self.GAIN
            cmd_y = current_ee['y'] + error_y * self.GAIN
            cmd_z = current_ee['z'] + error_z * self.GAIN
            
            # 5. 속도 조절 (오차가 크면 빠르게, 작으면 느리게)
            if total_error < 3.0:
                speed = 15  # 정밀 모드
            elif total_error < 10.0:
                speed = 30  # 중간 속도
            else:
                speed = 60  # 빠른 접근
            
            # 6. 명령 전송
            move_robot(cmd_x, cmd_y, cmd_z, speed)
            
            # 7. 주기적 디버그 로그 (5초마다)
            elapsed = time.time() - start_time
            if int(elapsed * 2) % 10 == 0 and elapsed > 0.5:
                logging.debug(
                    f"[VisualServo] Phase={phase}, "
                    f"오차={total_error:.1f}cm, "
                    f"목표=({goal['x']:.1f}, {goal['y']:.1f}, {goal['z']:.1f}), "
                    f"현재=({current_ee['x']:.1f}, {current_ee['y']:.1f}, {current_ee['z']:.1f})"
                )
            
            # 8. 루프 주기 유지 (20Hz = 50ms)
            elapsed_loop = time.time() - loop_start
            sleep_time = (1.0 / self.LOOP_HZ) - elapsed_loop
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        logging.warning("[VisualServo] 취소됨 (cancel_token)")
        return False
    
    def _transition(self, next_state: ServoState):
        """상태 전이 및 로깅"""
        logging.info(f"[VisualServoing] 상태 전환: {self.current_state.name} → {next_state.name}")
        self.current_state = next_state

# 싱글톤 인스턴스
visual_servoing = VisualServoing()
