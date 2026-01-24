import requests
import socketio
import numpy as np

# 서버 접속 정보
SERVER_URL = "http://localhost:5000"

class PybulletClient:
    """
    파이불렛 서버와 통신하여 리소스를 수집하는 실무형 클라이언트입니다.
    """
    def __init__(self):
        self.sio = socketio.Client()
        self.register_handlers()

    def register_handlers(self):
        @self.sio.event
        def connect():
            print("성공: 파이불렛 서버와 웹소켓 연결이 수립되었습니다.")

        @self.sio.event
        def disconnect():
            print("경고: 서버와의 연결이 해제되었습니다.")

    def connect(self):
        try:
            self.sio.connect(SERVER_URL)
        except Exception as e:
            print(f"연결 오류: {e}")

    def get_rgb_frame(self) -> Optional[np.ndarray]:
        """최신 RGB 이미지를 가져옵니다."""
        try:
            import cv2
            response = requests.get(f"{SERVER_URL}/image", timeout=1.0)
            if response.status_code == 200:
                img_array = np.frombuffer(response.content, dtype=np.uint8)
                return cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        except Exception:
            return None
        return None

    def get_depth_frame(self) -> Optional[np.ndarray]:
        """최신 Depth 데이터를 가져옵니다. (JSON 파싱 포함)"""
        try:
            response = requests.get(f"{SERVER_URL}/depth", timeout=5.0)
            if response.status_code == 200:
                return np.array(response.json(), dtype=np.float32)
        except Exception:
            return None
        return None

    def disconnect(self):
        if self.sio.connected:
            self.sio.disconnect()