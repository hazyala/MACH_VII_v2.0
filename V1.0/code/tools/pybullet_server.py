import socketio
import requests
import numpy as np
import cv2

class PyBulletServer:
    """
    MACH_SEVEN 본진과 파이불렛 연무장 서버 간의 실시간 통신을 담당하는 클래스입니다.
    웹 소켓(SocketIO)을 통해 끊김 없는 데이터 송수신을 지원합니다.
    """
    def __init__(self, ip="127.0.0.1", port=5000):
        # 서버 접속 기본 주소 설정
        self.base_url = f"http://{ip}:{port}"
        self.sio = socketio.Client()
        
        # 서버로부터 받은 최신 로봇 및 오브젝트 상태를 저장하는 변수
        self.robot_state = None
        self.object_state = None

        # 이벤트 핸들러 등록
        self._setup_event_handlers()

    def _setup_event_handlers(self):
        """서버로부터 전송되는 실시간 이벤트를 수신하기 위한 설정입니다."""
        @self.sio.event
        def connect():
            print("연무장 서버와 연결되었습니다.")

        @self.sio.on('robot_state')
        def on_robot_state(data):
            # 서버에서 보내주는 로봇의 최신 좌표와 조인트 각도를 저장합니다.
            self.robot_state = data

        @self.sio.on('object_state')
        def on_object_state(data):
            # 서버에서 보내주는 오브젝트의 상태 정보를 저장합니다.
            self.object_state = data

        @self.sio.event
        def disconnect():
            print("서버와의 연결이 종료되었습니다.")

    def connect(self):
        """웹 소켓 서버에 연결을 시도합니다."""
        try:
            self.sio.connect(self.base_url)
        except Exception as e:
            print(f"서버 연결 실패: {e}")

    def get_rgb_image(self):
        """이미지 데이터는 용량이 크므로 기존 HTTP GET 방식을 유지하여 가져옵니다."""
        try:
            r = requests.get(f"{self.base_url}/image", timeout=1)
            if r.status_code == 200:
                img_array = np.frombuffer(r.content, np.uint8)
                return cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        except Exception as e:
            print(f"이미지 수신 실패: {e}")
        return None

    def get_depth_data(self):
        """깊이 데이터(Depth Map)를 HTTP GET 방식으로 가져와 numpy 배열로 변환합니다."""
        try:
            r = requests.get(f"{self.base_url}/depth", timeout=1)
            if r.status_code == 200:
                return np.array(r.json(), dtype=np.float32)
        except Exception as e:
            print(f"깊이 데이터 수신 실패: {e}")
        return None

    def move_arm(self, position):
        """로봇팔을 목표 좌표 [x, y, z]로 이동시키라는 명령을 보냅니다."""
        if self.sio.connected:
            self.sio.emit('set_pos', {"pos": position})
            return True
        return False

    def get_arm_position(self):
        """이미 수신된 최신 로봇 상태에서 엔드이펙터 좌표를 반환합니다."""
        if self.robot_state:
            return self.robot_state.get("ee")
        return None

    def control_object(self, name, op="create", fix=False):
        """연무장에 물체를 생성하거나 제거하는 명령을 보냅니다."""
        if self.sio.connected:
            body = {"op": op, "object": name, "fix": fix}
            self.sio.emit('set_object', body)
            return True
        return False