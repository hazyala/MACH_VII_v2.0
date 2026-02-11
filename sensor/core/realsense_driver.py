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
        
        # [메인 카메라] 기본 RealSense 카메라 (고정 설치)
        self.running = False
        self.thread = None
        self.pipeline = None
        self.config = None
        
        # [그리퍼 카메라] 엔드 이펙터 장착 카메라 (선택적)
        self.gripper_running = False
        self.gripper_thread = None
        self.gripper_pipeline = None
        self.gripper_config = None
        
        # [IMU 데이터] 가속도/자이로 센서 (선택적)
        self.imu_data = {"accel": {"x": 0, "y": 0, "z": 0}, "gyro": {"x": 0, "y": 0, "z": 0}}
        self.imu_lock = threading.Lock()
        
        # [카메라 내인자] 정밀 좌표 변환을 위한 SDK 값
        self.intrinsics = {"fx": 605.0, "fy": 605.0, "cx": 320.0, "cy": 240.0}
        self.raw_intrinsics = None
        self.gripper_intrinsics = {"fx": 605.0, "fy": 605.0, "cx": 320.0, "cy": 240.0}
        self.gripper_raw_intrinsics = None
        
        # [프레임 버퍼] 메인 카메라
        self.latest_color = None
        self.latest_depth = None
        self.frame_lock = threading.Lock()
        
        # [프레임 버퍼] 그리퍼 카메라
        self.gripper_latest_color = None
        self.gripper_latest_depth = None
        self.gripper_frame_lock = threading.Lock()
        
        logging.info(f"[Sensor] RealSense 드라이버 초기화 완료 (SDK 가용: {RS_AVAILABLE})")
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

    def start_gripper_camera(self):
        """
        그리퍼 카메라 파이프라인을 구성하고 백그라운드 캡처 스레드를 시작합니다.
        메인 카메라와 독립적으로 동작합니다.
        """
        from shared.config import GlobalConfig
        
        if not GlobalConfig.REALSENSE_ENABLE_GRIPPER_CAM:
            logging.info("[Sensor] 그리퍼 카메라가 비활성화되어 있습니다.")
            return
            
        if not RS_AVAILABLE:
            logging.error("[Sensor] RealSense SDK를 찾을 수 없습니다.")
            return
            
        if self.gripper_running: return
        
        try:
            # 그리퍼 카메라용 별도 파이프라인 생성
            self.gripper_pipeline = rs.pipeline()
            self.gripper_config = rs.config()
            
            # 그리퍼 카메라 시리얼 번호로 특정 카메라 지정 (선택 사항)
            # self.gripper_config.enable_device('시리얼번호')
            
            self.gripper_config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, self.fps)
            self.gripper_config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, self.fps)
            
            self.gripper_pipeline.start(self.gripper_config)
            
            # Intrinsics 추출
            profile = self.gripper_pipeline.get_active_profile()
            color_stream = profile.get_stream(rs.stream.color).as_video_stream_profile()
            self.gripper_raw_intrinsics = color_stream.get_intrinsics()
            
            self.gripper_intrinsics = {
                "fx": self.gripper_raw_intrinsics.fx,
                "fy": self.gripper_raw_intrinsics.fy,
                "cx": self.gripper_raw_intrinsics.ppx,
                "cy": self.gripper_raw_intrinsics.ppy
            }
            
            self.gripper_running = True
            self.gripper_thread = threading.Thread(target=self._gripper_capture_loop, daemon=True)
            self.gripper_thread.start()
            logging.info(f"[Sensor] 그리퍼 카메라 시작 완료: {self.gripper_intrinsics}")
        except Exception as e:
            logging.error(f"[Sensor] 그리퍼 카메라 초기화 실패: {e}")
            self.gripper_pipeline = None
            self.gripper_running = False

    def stop(self):
        """
        모든 하드웨어 파이프라인을 안전하게 닫고 스레드를 종료합니다.
        """
        # 메인 카메라 종료
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        
        if self.pipeline:
            try:
                self.pipeline.stop()
            except Exception as e:
                logging.warning(f"[Sensor] 메인 파이프라인 종료 중 예외 발생: {e}")
            self.pipeline = None
            
        # 그리퍼 카메라 종료
        self.gripper_running = False
        if self.gripper_thread:
            self.gripper_thread.join(timeout=2.0)
            
        if self.gripper_pipeline:
            try:
                self.gripper_pipeline.stop()
            except Exception as e:
                logging.warning(f"[Sensor] 그리퍼 파이프라인 종료 중 예외 발생: {e}")
            self.gripper_pipeline = None
            
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

    def _gripper_capture_loop(self):
        """
        [인터널] 그리퍼 카메라로부터 지속적으로 프레임을 읽어와 버퍼를 갱신하는 루프입니다.
        """
        while self.gripper_running:
            try:
                frames = self.gripper_pipeline.wait_for_frames(timeout_ms=1000)
                depth_frame = frames.get_depth_frame()
                color_frame = frames.get_color_frame()
                
                if not depth_frame or not color_frame:
                    continue

                color_image = np.asanyarray(color_frame.get_data())
                depth_image = np.asanyarray(depth_frame.get_data())

                with self.gripper_frame_lock:
                    self.gripper_latest_color = color_image
                    self.gripper_latest_depth = depth_image
                    
                # IMU 데이터 획득 (같은 프레임셋에 포함되어 있을 수 있음)
                from shared.config import GlobalConfig
                if GlobalConfig.REALSENSE_ENABLE_IMU:
                    self._update_imu_data(frames)
                    
            except Exception as e:
                logging.warning(f"[Sensor] 그리퍼 카메라 캡처 중 오류 발생: {e}")
                time.sleep(0.5)

            time.sleep(1.0 / self.fps)

    def _update_imu_data(self, frames):
        """
        [인터널] 프레임셋에서 IMU 데이터(가속도/자이로)를 추출하여 업데이트합니다.
        """
        try:
            # 가속도 데이터
            accel_frame = frames.first_or_default(rs.stream.accel)
            if accel_frame:
                accel_data = accel_frame.as_motion_frame().get_motion_data()
                with self.imu_lock:
                    self.imu_data["accel"] = {
                        "x": accel_data.x,
                        "y": accel_data.y,
                        "z": accel_data.z
                    }
            
            # 자이로 데이터
            gyro_frame = frames.first_or_default(rs.stream.gyro)
            if gyro_frame:
                gyro_data = gyro_frame.as_motion_frame().get_motion_data()
                with self.imu_lock:
                    self.imu_data["gyro"] = {
                        "x": gyro_data.x,
                        "y": gyro_data.y,
                        "z": gyro_data.z
                    }
        except Exception as e:
            logging.debug(f"[Sensor] IMU 데이터 추출 실패 (일부 모델 미지원): {e}")

    def get_frames(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """현재 가장 최신의 메인 카메라 RGB 및 Depth 프레임을 반환합니다."""
        with self.frame_lock:
            return self.latest_color, self.latest_depth

    def get_gripper_frames(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """현재 가장 최신의 그리퍼 카메라 RGB 및 Depth 프레임을 반환합니다."""
        with self.gripper_frame_lock:
            return self.gripper_latest_color, self.gripper_latest_depth

    def get_imu_data(self) -> dict:
        """현재 IMU 데이터(가속도/자이로)를 반환합니다."""
        with self.imu_lock:
            return self.imu_data.copy()

    def get_intrinsics(self) -> dict:
        """SDK에서 읽어온 실제 카메라 내인자(Intrinsics: 렌즈 파라미터) 값을 딕셔너리로 반환합니다."""
        return self.intrinsics

    def get_raw_intrinsics(self):
        """메인 카메라 SDK의 로우 내인자(Raw Intrinsics)를 반환합니다."""
        return self.raw_intrinsics

    def get_gripper_intrinsics(self) -> dict:
        """그리퍼 카메라의 내인자를 딕셔너리로 반환합니다."""
        return self.gripper_intrinsics

    def get_gripper_raw_intrinsics(self):
        """그리퍼 카메라 SDK의 로우 내인자를 반환합니다."""
        return self.gripper_raw_intrinsics

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

    def generate_gripper_stream(self):
        """
        그리퍼 카메라의 Web UI 실시간 스트리밍을 위한 MJPEG 데이터 생성기입니다.
        """
        while True:
            color, _ = self.get_gripper_frames()
            if color is not None:
                ret, buffer = cv2.imencode('.jpg', color, [cv2.IMWRITE_JPEG_QUALITY, 60])
                if ret:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            time.sleep(1.0 / self.fps)

# 전역 인스턴스 노출 (싱글톤 정책 준수)
realsense_driver = RealSenseDriver()
