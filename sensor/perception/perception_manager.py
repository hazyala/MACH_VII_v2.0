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
                # 1. 시각 탐지 및 3D 좌표 산출
                # VisionBridge를 통해 필터링된 객체 리스트를 가져옵니다.
                detections = self.bridge.get_refined_detections()
                
                # 2. VLM 분석용 프레임 획득 및 인코딩
                # Brain Layer의 시각 분석(VLM: Visual-Language Model - 영상을 보고 상황을 설명해주는 시각-언어 모델)을 위해 
                # 원본 영상을 Base64(텍스트 형태의 데이터 변환 방식)로 미리 준비합니다.
                raw_frame = self.bridge.get_raw_frame()
                image_b64 = None
                if raw_frame is not None:
                     # 전송량 최적화를 위해 JPEG 품질을 70%로 조정하여 인코딩
                     ret, buffer = cv2.imencode('.jpg', raw_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                     if ret:
                         image_b64 = base64.b64encode(buffer).decode('utf-8')

                # 3. 전역 상태(Layer 2: State) 업데이트
                # 모든 레이어가 공통으로 참조하는 system_state에 인지 결과 기록
                new_perception = {
                    "detected_objects": detections,
                    "detection_count": len(detections),
                    "timestamp": time.time(),
                    "sensor_mode": "Sim" if GlobalConfig.SIM_MODE else "Real"
                }
                
                system_state.perception_data = new_perception
                if image_b64:
                    system_state.last_frame_base64 = image_b64
                
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
