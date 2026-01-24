import requests
import socketio
import numpy as np
import cv2
from typing import Optional, Dict, Any

# 파이불렛 서버 주소 설정
SERVER_URL = "http://localhost:5000"

class PybulletClient:
    """
    파이불렛 서버와 통신하여 영상, 깊이, 로봇 포즈 데이터를 수집하는 클라이언트 클래스입니다.
    데이터 간의 시간적 동기화를 보장하는 기능을 포함합니다.
    """
    def __init__(self):
        # 웹소켓 클라이언트 초기화 및 이벤트 핸들러 등록
        self.sio = socketio.Client()
        self.register_handlers()

    def register_handlers(self):
        """웹소켓 연결 및 해제 시 발생하는 이벤트를 처리합니다."""
        @self.sio.event
        def connect():
            print("INFO: 파이불렛 서버와 웹소켓 연결이 수립되었습니다.")

        @self.sio.event
        def disconnect():
            print("WARN: 서버와의 연결이 해제되었습니다.")

    def connect(self):
        """설정된 서버 URL로 웹소켓 연결을 시도합니다."""
        try:
            self.sio.connect(SERVER_URL)
        except Exception as e:
            print(f"ERROR: 서버 연결 중 오류 발생: {e}")

    def get_rgb_frame(self) -> Optional[np.ndarray]:
        """서버로부터 최신 RGB 영상을 획득하여 numpy 배열로 반환합니다."""
        try:
            response = requests.get(f"{SERVER_URL}/image", timeout=1.0)
            if response.status_code == 200:
                img_array = np.frombuffer(response.content, dtype=np.uint8)
                return cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        except Exception as e:
            print(f"ERROR: RGB 프레임 획득 실패: {e}")
        return None

    def get_depth_frame(self) -> Optional[np.ndarray]:
        """서버로부터 최신 깊이(Depth) 데이터를 획득하여 numpy 배열로 반환합니다."""
        try:
            response = requests.get(f"{SERVER_URL}/depth", timeout=2.0)
            if response.status_code == 200:
                return np.array(response.json(), dtype=np.float32)
        except Exception as e:
            print(f"ERROR: 깊이 데이터 획득 실패: {e}")
        return None

    def get_robot_pose(self) -> Optional[Dict[str, float]]:
        """
        서버로부터 현재 로봇의 포즈를 가져옵니다.
        서버의 미터(m) 단위를 시스템 표준인 센티미터(cm)로 변환합니다.
        """
        try:
            response = requests.get(f"{SERVER_URL}/get_pose", timeout=1.0)
            if response.status_code == 200:
                data = response.json()
                pos = data.get("pos", [0.0, 0.0, 0.0])
                # m 단위를 cm 단위로 변환 (1.0m -> 100.0cm)
                return {
                    "x": pos[0] * 100.0,
                    "y": pos[1] * 100.0,
                    "z": pos[2] * 100.0
                }
        except Exception as e:
            print(f"ERROR: 로봇 포즈 획득 실패: {e}")
        return None

    def get_synced_packet(self) -> Optional[Dict[str, Any]]:
        """
        영상, 깊이, 로봇 포즈를 거의 동일한 시점에 획득하여 동기화된 패키지로 반환합니다.
        비주얼 서보잉의 정밀도를 높이기 위해 사용됩니다.
        """
        try:
            # 개별 데이터들을 순차적으로 빠르게 요청합니다.
            color = self.get_rgb_frame()
            depth = self.get_depth_frame()
            pose = self.get_robot_pose()

            if color is not None and depth is not None and pose is not None:
                return {
                    "color": color,
                    "depth": depth,
                    "captured_pose": pose
                }
        except Exception as e:
            print(f"ERROR: 동기화 패키지 구성 실패: {e}")
        return None