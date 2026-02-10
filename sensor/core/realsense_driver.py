import time
import threading
import numpy as np
import logging
import cv2
from typing import Optional, Tuple

# 1. RealSense SDK(pyrealsense2) 라이브러리 가용성 체크
# 하드웨어가 없거나 라이브러리가 설치되지 않은 환경에서도 시스템이 정상 작동하도록 합니다.
RS_AVAILABLE = False
try:
    import pyrealsense2 as rs
    RS_AVAILABLE = True
except ImportError:
    RS_AVAILABLE = False

class RealSenseDriver:
    """
    [Layer 1: Sensor] RealSense 하드웨어 전용 저수준 드라이버입니다.
    
    이 클래슨는 Intel RealSense 카메라와 직접 통신하여 RGB 및 Depth 프레임을 획득합니다.
    AI 분석이나 고수준 인지 로직 없이 오직 '데이터 획득'과 '스레드 안전한 제공'에만 집중합니다.

    * RealSense SDK를 통해 다음과 같은 추가 확장 예정입니다.
    1. 기울기 및 각도 (Pitch, Roll): 
       - 가속도/자이로 데이터를 통해 지면 대비 기울기 획득 가능한 모델 사용중으로 구현 가능
       - [구현 예정] SDK의 Motion Stream(모션 스트림: 기울기나 가속도 등 움직임 정보)을 활성화하여 실시간 카메라 자세(Pose) 추출 로직 추가 가능.
    2. 정밀 정합 (Extrinsics: 카메라와 센서 간의 위치 및 각도 등 외부 정렬 상태):
       - 카메라 내부의 RGB 센서와 Depth 센서 간의 미세한 물리적 오프셋을 SDK에서 직접 가져와 보정 가능.
    3. 로봇 베이스 정합:
       - 카메라가 로봇 대비 설치된 각도는 로봇 관절 상태와 결합해야 하므로, 이는 VisionBridge 계층에서 관리함.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """
        패턴: Thread-safe Singleton (스레드 안전한 싱글톤: 여러 작업이 동시에 접근해도 단 하나의 인스턴스만 생성되도록 보장하는 방식)
        전체 시스템에서 단 하나의 RealSense 드라이버 인스턴스만 존재해야 하므로 싱글톤을 적용합니다.
        """
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(RealSenseDriver, cls).__new__(cls)
        return cls._instance

    def __init__(self, fps=30):
        """
        드라이버 파라미터 및 프레임 버퍼를 초기화합니다.
        """
        if hasattr(self, 'initialized') and self.initialized:
            return
            
        self.fps = fps
        self.running = False
        self.thread = None
        self.pipeline = None
        self.config = None
        
        # [카메라 내인자] 정밀 좌표 변환을 위한 SDK 값 (Intrinsics: 렌즈 고유의 초점 거리나 중심점 등 카메라 내부 속성)
        self.intrinsics = {"fx": 605.0, "fy": 605.0, "cx": 320.0, "cy": 240.0}
        self.raw_intrinsics = None # SDK raw object (pyrealsense2.intrinsics: 렌즈 왜곡 정보가 포함된 원본 내부 파라미터 객체)
        
        # [프레임 버퍼] 최신 프레임을 저장하고 여러 레이어에서 안전하게 읽어갈 수 있도록 합니다.
        self.latest_color = None
        self.latest_depth = None
        self.frame_lock = threading.Lock() # 읽기/쓰기 충돌 방지용 락
        
        logging.info(f"[Sensor] RealSense 드라이버 초기체 완료 (가용여부: {RS_AVAILABLE})")
        self.initialized = True

    def start(self):
        """
        카메라 파이프라인을 구성하고 백그라운드 캡처 스레드를 시작합니다.
        """
        if not RS_AVAILABLE:
            logging.error("[Sensor] RealSense SDK를 찾을 수 없습니다. 카메라를 시작할 수 없습니다.")
            return

        if self.running: return

        try:
            # 파이프라인 및 스트림 설정 (640x480 QVGA 해상도 기준)
            self.pipeline = rs.pipeline()
            self.config = rs.config()
            self.config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, self.fps)
            self.config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, self.fps)
            
            # 하드웨어 시작
            self.pipeline.start(self.config)
            
            # [Intrinsics 추출] 활성 프로필에서 실제 카메라 파라미터(내인자)를 읽어옵니다.
            profile = self.pipeline.get_active_profile()
            color_stream = profile.get_stream(rs.stream.color).as_video_stream_profile()
            self.raw_intrinsics = color_stream.get_intrinsics()
            
            self.intrinsics = {
                "fx": self.raw_intrinsics.fx,
                "fy": self.raw_intrinsics.fy,
                "cx": self.raw_intrinsics.ppx,
                "cy": self.raw_intrinsics.ppy
            }
            logging.info(f"[Sensor] RealSense Intrinsics(내인자) 추출 완료: {self.intrinsics}")

            self.running = True
            
            # [백그라운드 스레드] 메인 루프에 지장을 주지 않도록 별도 스레드에서 영상을 획득합니다.
            self.thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.thread.start()
            logging.info("[Sensor] RealSense 하드웨어 캡처 루프 가동 시작.")
        except Exception as e:
            logging.error(f"[Sensor] RealSense 하드웨어 초기화 실패: {e}")
            self.pipeline = None
            self.running = False

    def stop(self):
        """
        하드웨어 파이프라인을 안전하게 닫고 스레드를 종료합니다.
        """
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        
        if self.pipeline:
            try:
                self.pipeline.stop()
            except Exception as e:
                logging.warning(f"[Sensor] 파이프라인 종료 중 예외 발생: {e}")
            self.pipeline = None
        logging.info("[Sensor] RealSense 드라이버가 안전하게 중지되었습니다.")

    def _capture_loop(self):
        """
        [인터널] 하드웨어로부터 지속적으로 프레임을 읽어와 버퍼를 갱신하는 루프입니다.
        """
        while self.running:
            try:
                # 최대 1초 동안 프레임을 기다립니다.
                frames = self.pipeline.wait_for_frames(timeout_ms=1000)
                depth_frame = frames.get_depth_frame()
                color_frame = frames.get_color_frame()
                
                if not depth_frame or not color_frame:
                    continue

                # SDK 데이터를 Numpy 배열로 변환
                color_image = np.asanyarray(color_frame.get_data())
                depth_image = np.asanyarray(depth_frame.get_data())

                # [Lock] 버퍼 업데이트 시 스레드 동기화(동시 접근 방지) 보장
                with self.frame_lock:
                    self.latest_color = color_image
                    self.latest_depth = depth_image
                    
            except Exception as e:
                logging.warning(f"[Sensor] 캡처 중 하드웨어 오류 발생: {e}")
                time.sleep(0.5) # 오류 발생 시 재시도 대기시간 연장

            time.sleep(1.0 / self.fps)

    def get_frames(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """현재 가장 최신의 RGB 및 Depth 프레임을 반환합니다."""
        with self.frame_lock:
            return self.latest_color, self.latest_depth

    def get_intrinsics(self) -> dict:
        """SDK에서 읽어온 실제 카메라 내인자(Intrinsics: 렌즈 파라미터) 값을 딕셔너리로 반환합니다."""
        return self.intrinsics

    def get_raw_intrinsics(self):
        """SDK의 로우 내인자(Raw Intrinsics: 왜곡 정보가 포함된 원본 객체)를 반환합니다. (공식 역투영 함수용)"""
        return self.raw_intrinsics

    def generate_rgb_stream(self):
        """
        Web UI의 실시간 스트리밍을 위한 MJPEG 데이터 생성기입니다.
        """
        while True:
            color, _ = self.get_frames()
            if color is not None:
                # 성능 및 대역폭을 고려하여 60% 품질로 인코딩
                ret, buffer = cv2.imencode('.jpg', color, [cv2.IMWRITE_JPEG_QUALITY, 60])
                if ret:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            time.sleep(1.0 / self.fps)

# 전역 인스턴스 노출 (싱글톤 정책 준수)
realsense_driver = RealSenseDriver()
