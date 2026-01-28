import time
import threading
import numpy as np
import logging
from typing import Dict, Any
from shared.state_broadcaster import broadcaster
import cv2 # OpenCV added for encoding
from ultralytics import YOLO # YOLOv8
import torch
import requests # For fetching PyBullet frames
import logging


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
            "risk_level": "SAFE",
            "active_source": "PyBullet"
        }
        self.target_source = "PyBullet" # RealSense, PyBullet, WebCam
        self.latest_color_jpeg = None
        self.latest_depth_jpeg = None
        self.frame_lock = threading.Lock() # Lock for frame access
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
            
            # YOLO Load (Lazy)
            try:
                self.yolo_model = YOLO("yolov8n.pt") # Nano model for speed
                logging.info("[RealSense] YOLOv8 Model Loaded")
            except Exception as e:
                logging.error(f"[RealSense] YOLO Load Failed: {e}")
                self.yolo_model = None

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
            
            # Unified Frame Capture Logic
            color_image = None
            depth_colormap = None
            center_dist = 0.0

            if self.target_source == "PyBullet":
                # Fetch from PyBullet Server (Snapshot)
                try:
                    # Request the SNAPSHOT endpoint (not stream) to get one frame
                    resp = requests.get("http://localhost:5000/image", timeout=0.5)
                    if resp.status_code == 200:
                        # Decode
                        arr = np.frombuffer(resp.content, np.uint8)
                        color_image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                        # PyBullet depth? We can fetch /depth if needed, but let's mock depth or fetch it
                        # For now, just black depth or fetch if fast enough
                        depth_colormap = np.zeros((480, 640, 3), dtype=np.uint8)
                except Exception as e:
                    # PyBullet connection failed -> Show Error Frame
                    color_image = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(color_image, "PYBULLET DISCONNECTED", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    depth_colormap = np.zeros((480, 640, 3), dtype=np.uint8)

            elif self.target_source == "RealSense" and RS_AVAILABLE and self.pipeline:
                # Hardware Capture
                try:
                    frames = self.pipeline.wait_for_frames(timeout_ms=1000)
                    depth_frame = frames.get_depth_frame()
                    color_frame = frames.get_color_frame()
                    if depth_frame and color_frame:
                         depth_image = np.asanyarray(depth_frame.get_data())
                         color_image = np.asanyarray(color_frame.get_data())
                         
                         width = depth_frame.get_width()
                         height = depth_frame.get_height()
                         # Center Dist Logic
                         center_dist = depth_frame.get_distance(width // 2, height // 2) * 100
                         
                         depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_image, alpha=0.03), cv2.COLORMAP_JET)
                except:
                     pass
            
            # If no frame (Mock or Error)
            if color_image is None:
                # Mock Generation
                 color_image = np.zeros((480, 640, 3), dtype=np.uint8)
                 cv2.putText(color_image, f"[MOCK] Source: {self.target_source}", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                 depth_colormap = np.zeros((480, 640, 3), dtype=np.uint8)

            # --- Common Processing (YOLO) ---
            detections = []
            if self.yolo_model and color_image is not None:
                results = self.yolo_model(color_image, verbose=False)
                for result in results:
                    boxes = result.boxes
                    for box in boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        conf = float(box.conf[0])
                        cls = int(box.cls[0])
                        label_name = self.yolo_model.names[cls]
                        label = f"{label_name} {conf:.2f}"
                        
                        detections.append({
                            "label": label_name,
                            "confidence": conf,
                            "bbox": [x1, y1, x2, y2]
                        })

                        # Draw
                        cv2.rectangle(color_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(color_image, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Encode
            ret, c_jpg = cv2.imencode('.jpg', color_image, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
            ret2, d_jpg = cv2.imencode('.jpg', depth_colormap, [int(cv2.IMWRITE_JPEG_QUALITY), 50])

            # VLM 분석용 Base64 생성 (비용 절감을 위해 필요할 때만 하거나, 여기서 미리 해둠 - 최적화는 추후)
            import base64
            b64_image = None
            if ret:
                b64_image = base64.b64encode(c_jpg).decode('utf-8')

            with self.frame_lock:
                if ret: self.latest_color_jpeg = c_jpg.tobytes()
                if ret2: self.latest_depth_jpeg = d_jpg.tobytes()
            
            # Update Perception State
            self._update_perception(center_dist, detections, image_b64=b64_image, mode=self.target_source)

            # Throttle
            dt = time.time() - start_time
            sleep_time = max(0, (1.0 / self.fps) - dt)
            time.sleep(sleep_time)

        logging.info("[RealSense] 루프 종료됨.")

    def set_source(self, source_name):
        logging.info(f"[RealSense] Source switched to {source_name}")
        self.target_source = source_name

    def _update_perception(self, distance_cm: float, detections: list, image_b64: str = None, grid: list = None, mode: str = "UNKNOWN"):
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
            "detection_count": len(detections),
            "detected_objects": detections, # YOLO 결과 리스트
            "risk_level": str(risk),
            "sensor_mode": str(mode)
        }
        
        self.latest_state = new_state
        
        # SystemState Single Source of Truth 업데이트
        from state.system_state import system_state
        system_state.perception_data = new_state
        if image_b64:
            system_state.last_frame_base64 = image_b64
            
        broadcaster.publish("perception", new_state)

    def get_state(self) -> Dict[str, Any]:
        return self.latest_state
        
    def generate_rgb_stream(self):
        while True:
            with self.frame_lock:
                frame = self.latest_color_jpeg
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.033) # 30fps cap
            
    def generate_depth_stream(self):
        while True:
            with self.frame_lock:
                frame = self.latest_depth_jpeg
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.033)

# 전역 인스턴스
realsense_driver = RealSenseDriver()
