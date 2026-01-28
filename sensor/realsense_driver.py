import time
import threading
import numpy as np
import logging
from typing import Dict, Any
from shared.state_broadcaster import broadcaster

# 1. 전역 상수 선언 (안전)
RS_AVAILABLE = False
try:
    import pyrealsense2 as rs
    RS_AVAILABLE = True
except ImportError:
    RS_AVAILABLE = False
except Exception:
    RS_AVAILABLE = False

class RealSenseDriver:
    """
    RealSense 카메라의 생명주기를 안전하게 관리하는 클래스입니다.
    모듈 레벨 인스턴스화를 통해 싱글톤 패턴을 보장합니다.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(RealSenseDriver, cls).__new__(cls)
        return cls._instance

    def __init__(self, fps=30):
        # 이미 초기화된 경우 재초기화 방지
        if hasattr(self, 'initialized') and self.initialized:
            return
            
        self.fps = fps
        self.running = False
        self.thread = None
        self.state_lock = threading.Lock()
        self.latest_state = {
            "obstacle_distance_cm": 0.0,
            "human_detected": False,
            "risk_level": "SAFE"
        }
        self.pipeline = None
        self.config = None
        
        logging.info(f"[RealSense] 드라이버 인스턴스 생성됨. RS_AVAILABLE={RS_AVAILABLE}")
        self.initialized = True

    def start(self):
        # 3. 멱등성 및 스레드 안전성 보장
        with self.state_lock:
            if self.running:
                logging.warning("[RealSense] 드라이버가 이미 실행 중입니다. start() 요청 무시됨.")
                return

            self.running = True
            
            # 하드웨어 설정 (지연 초기화 Lazy Init)
            if RS_AVAILABLE:
                try:
                    if self.pipeline is None:
                        self.pipeline = rs.pipeline()
                        self.config = rs.config()
                        self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
                        self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
                    
                    # 파이프라인 활성화 상태 확인 (일부 rs 버전은 두 번 시작 시 예외 발생)
                    # 안전을 위해 start를 try/except로 감쌈
                    self.pipeline.start(self.config)
                    logging.info("[RealSense] 파이프라인 시작됨.")
                except Exception as e:
                    logging.error(f"[RealSense] 초기화 실패: {e}. MOCK 모드로 전환합니다.")
                    self.pipeline = None # Mock 모드 강제 설정
            
            # 스레드 시작
            if self.thread is None or not self.thread.is_alive():
                self.thread = threading.Thread(target=self._sensor_loop, daemon=True)
                self.thread.start()
                logging.info("[RealSense] 센서 루프 시작됨.")

    def stop(self):
        with self.state_lock:
            if not self.running:
                return
                
            self.running = False
            logging.info("[RealSense] 드라이버 중지 중...")

        # 데드락 방지를 위해 락 외부에서 스레드 조인
        if self.thread:
            self.thread.join(timeout=2.0)
            self.thread = None

        # 하드웨어 중지
        if self.pipeline and RS_AVAILABLE:
            try:
                self.pipeline.stop()
            except Exception as e:
                logging.error(f"[RealSense] 파이프라인 중지 오류: {e}")
            finally:
                self.pipeline = None # 다음 시작 시 새로운 init을 위해 파이프라인 초기화

    def _sensor_loop(self):
        logging.info("[RealSense] 루프 실행 중...")
        while self.running:
            start_time = time.time()
            
            # 모드 결정
            use_hardware = RS_AVAILABLE and (self.pipeline is not None)
            
            if use_hardware:
                try:
                    frames = self.pipeline.wait_for_frames(timeout_ms=1000)
                    depth_frame = frames.get_depth_frame()
                    if depth_frame:
                        width = depth_frame.get_width()
                        height = depth_frame.get_height()
                        
                        # 3x3 격자 샘플링
                        grid = []
                        rows = cols = 3
                        w_step = width // cols
                        h_step = height // rows
                        
                        center_dist = 0.0
                        
                        for r in range(rows):
                            for c in range(cols):
                                # 각 셀의 중심점 샘플링
                                cx = c * w_step + w_step // 2
                                cy = r * h_step + h_step // 2
                                d = depth_frame.get_distance(cx, cy)
                                grid.append(float(d * 100)) # cm 단위 변환
                                
                                # 중앙 셀(인덱스 4)을 주 거리로 사용
                                if r == 1 and c == 1:
                                    center_dist = d * 100

                        self._update_perception(center_dist, grid, mode="REAL")
                except RuntimeError as e:
                    logging.warning(f"[RealSense] 런타임 오류 (타임아웃?): {e}")
                except Exception as e:
                    logging.error(f"[RealSense] 예상치 못한 오류: {e}")
            else:
                # Mock(모의) 데이터
                # 격자를 지나가는 움직이는 물체 시뮬레이션
                t = time.time()
                mock_grid = [100.0] * 9
                
                # 움직이는 파동(Wave)
                wave_idx = int(t * 2) % 9
                mock_grid[wave_idx] = 20.0 # 가까운 물체
                
                sim_dist = mock_grid[4] # 중앙
                self._update_perception(sim_dist, mock_grid, mode="MOCK")
                time.sleep(1.0 / self.fps)

            # 속도 조절 (Throttle)
            dt = time.time() - start_time
            sleep_time = max(0, (1.0 / self.fps) - dt)
            time.sleep(sleep_time)
        
        logging.info("[RealSense] 루프 종료됨.")

    def _update_perception(self, distance_cm: float, grid: list = None, mode: str = "UNKNOWN"):
        risk = "SAFE"
        # 로직: 중앙 거리가 30cm 미만이면 -> DANGER
        # 또는 격자 셀 중 하나라도 20cm 미만이면? 일단 단순하게 유지
        if distance_cm > 0 and distance_cm < 30: 
            risk = "DANGER"
        elif distance_cm < 60 and distance_cm > 0:
            risk = "WARNING"
        elif distance_cm == 0:
             risk = "BLIND"
            
        new_state = {
            "obstacle_distance_cm": float(distance_cm), 
            "depth_grid": grid if grid else [0.0]*9, # 3x3 평탄화됨(Flattened)
            "human_detected": False, 
            "risk_level": str(risk),
            "sensor_mode": str(mode)
        }
        
        self.latest_state = new_state
        broadcaster.publish("perception", new_state)

    def get_state(self) -> Dict[str, Any]:
        return self.latest_state

# 전역 인스턴스
realsense_driver = RealSenseDriver()
