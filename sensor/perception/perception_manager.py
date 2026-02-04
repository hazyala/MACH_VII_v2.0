import threading
import time
import logging
import base64
import cv2
from .vision_bridge import VisionBridge
from state.system_state import system_state
from shared.state_broadcaster import broadcaster
from shared.config import GlobalConfig

class PerceptionManager:
    """
    [Layer 1: Sensor Management] 시각 인지 시스템의 최종 관리 클래스입니다.
    
    주기적으로 비전 데이터를 수집(Detection, Raw Frame 등)하여 전역 상태(Layer 2: State)를 업데이트하고,
    시스템의 다른 레이어들이 최신 비전 정보를 실시간으로 구독할 수 있도록 전파(Broadcast)합니다.
    """
    def __init__(self, interval: float = 0.1):
        """
        인지 루프 파라미터 및 비전 중계자를 초기화합니다.
        
        Args:
            interval: 업데이트 주기 (기본 0.1초 = 10Hz)
        """
        self.bridge = VisionBridge()
        self.interval = interval
        self.running = False
        self.thread = None

    def start(self):
        """
        백그라운드 인지 업데이트 루프를 시작합니다.
        """
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()
        logging.info("[PerceptionManager] 비전 인지 업데이트 루프 가동 시작.")

    def stop(self):
        """
        인지 업데이트 루프를 안전하게 종료합니다.
        """
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        logging.info("[PerceptionManager] 비전 인지 업데이트 루프 정지.")

    def _update_loop(self):
        """
        [Main Loop] 백그라운드에서 실시간으로 시각 정보를 수집하고 전파하는 핵심 루프입니다.
        """
        while self.running:
            loop_start_time = time.time()
            try:
                # 1. 시각 탐지 및 3D 좌표 산출 (Main Camera 기준)
                # VisionBridge를 통해 필터링된 객체 리스트와 당시의 프레임을 함께 가져옵니다.
                detections, main_frame = self.bridge.get_refined_detections()
                
                # 2. 전역 상태(Layer 2: State) 업데이트
                new_perception = {
                    "detected_objects": detections,
                    "detection_count": len(detections),
                    "timestamp": time.time(),
                    "sensor_mode": "Sim" if GlobalConfig.SIM_MODE else "Real"
                }
                system_state.perception_data = new_perception
                
                # [Optimization] 탐지에 사용된 동일 프레임을 Base64로 인코딩하여 UI 전달
                if main_frame is not None:
                     # 전송량 최적화를 위해 JPEG 품질을 75%로 조정
                     ret, buffer = cv2.imencode('.jpg', main_frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
                     if ret:
                         system_state.last_frame_base64 = base64.b64encode(buffer).decode('utf-8')
                    
                # 2-2. [Secondary Stream] 그리퍼 카메라 프레임 획득 (디버깅용)
                # 메인 뷰와 별개로 그리퍼의 시점을 상시 확보합니다.
                gripper_frame = self.bridge.get_gripper_frame()
                if gripper_frame is not None:
                     ret, buffer_ee = cv2.imencode('.jpg', gripper_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                     if ret:
                         system_state.last_ee_frame_base64 = base64.b64encode(buffer_ee).decode('utf-8')
                else:
                    # 그리퍼 카메라 미수신 시 상태 초기화 (옵션)
                    # system_state.last_ee_frame_base64 = None
                    pass
                
                # [Control Tower] 로봇 상태 동기화 및 안전 감시
                # 시뮬레이션 클라이언트로부터 최신 로봇 상태를 가져와 SystemState에 반영합니다.
                if GlobalConfig.SIM_MODE:
                    from interface.backend.sim_client import pybullet_client
                    with pybullet_client.lock:
                        robot_info = pybullet_client.latest_state.get('robot', {})
                    
                    # 관절 상태 및 그리퍼 상태 동기화
                    # robot_info 구조: {'joints': [...], 'ee': {...}, 'gripper': 0.05, 'status': 'IDLE'} 가정
                    system_state.robot.gripper_state = robot_info.get('gripper', 0.0)
                    
                    # 물리 엔진 상태(arm_status) 모니터링: "STUCK", "MOVING", "IDLE"
                    current_status = robot_info.get('status', 'IDLE')
                    system_state.robot.arm_status = current_status
                    
                    # Safety Loop: "STUCK" 상태 감지 시 즉시 안전 플래그 설정
                    if current_status == "STUCK":
                        system_state.robot.is_unsafe = True
                        logging.critical("[Control Tower] 🚨 로봇 끼임(STUCK) 감지! 안전 모드 발동됨.")
                    else:
                        system_state.robot.is_unsafe = False

                # 4. 상태 전파 (Layer 1 -> Other Layers)
                # UI나 다른 레이어에서 비전 이벤트를 실시간으로 처리할 수 있도록 알림 발행(Broadcasting: 여러 곳에 동시에 알림)
                broadcaster.publish("perception", new_perception)
                
            except Exception as e:
                logging.error(f"[PerceptionManager] 업데이트 루프 중 치명적 오류: {e}")
            
            # 실행 시간을 고려하여 정해진 주기를 유지 (Precision Loop: 정확한 실행 주기를 보장하는 기법)
            elapsed = time.time() - loop_start_time
            sleep_time = max(0, self.interval - elapsed)
            time.sleep(sleep_time)

# 전역 싱글톤 인스턴스 노출
# 시스템 어디서든 perception_manager를 통해 비전 루프를 제어할 수 있습니다.
perception_manager = PerceptionManager()
