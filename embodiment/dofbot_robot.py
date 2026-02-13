# embodiment/dofbot_robot.py

import logging
import socketio
import threading
import time
from typing import Tuple, Optional
from .robot_base import RobotBase
from shared.config import GlobalConfig

class DofbotRobot(RobotBase):
    """
    [Layer 6: Embodiment] DOFBOT 실물 로봇 클라이언트
    가장 단순하고 안정적인 형태의 초기 버전으로 롤백됨.
    """
    
    def __init__(self):
        self.sio = socketio.Client()
        self.server_url = GlobalConfig.DOFBOT_SERVER_URL
        self.connected = False
        self.latest_state = {}
        self.state_lock = threading.Lock()
        
        # 이벤트 등록
        self.sio.on('connect', self._on_connect)
        self.sio.on('disconnect', self._on_disconnect)
        self.sio.on('robot_state', self._on_robot_state)
        
        # [Simple Connect] 초기화 시 1회 시도
        self.connect()
        
    def connect(self):
        try:
            logging.info(f"[DofbotRobot] 연결 시도: {self.server_url}")
            self.sio.connect(self.server_url, transports=['websocket', 'polling'], wait_timeout=5)
            self.connected = True
        except Exception as e:
            logging.error(f"[DofbotRobot] 연결 실패: {e}")
            self.connected = False

    def disconnect(self):
        if self.connected:
            self.sio.disconnect()
            
    def _on_connect(self):
        self.connected = True
        logging.info("[DofbotRobot] 연결됨!")
        
    def _on_disconnect(self):
        self.connected = False
        logging.info("[DofbotRobot] 연결 끊김!")
        
    def _on_robot_state(self, data):
        with self.state_lock:
            self.latest_state = data
            
    def move_to(self, x: float, y: float, z: float, speed: float = 1.0, wait: bool = True) -> bool:
        if not self.connected:
            logging.warning("[DofbotRobot] 로봇 미연결 상태")
            # 연결 안 되어 있어도 일단 시도해볼 수 있음 (재연결 로직 제거)
            
        try:
            # cm -> m 변환
            pos_m = [x / 100.0, y / 100.0, z / 100.0]
            
            logging.info(f"[DofbotRobot] 이동: {x},{y},{z} -> {pos_m}")
            # 순수 데이터 전송
            self.sio.emit('set_pos', {'pos': pos_m})
            
            if wait:
                time.sleep(1.0) # 고정 대기
            return True
        except Exception as e:
            logging.error(f"[DofbotRobot] 이동 에러: {e}")
            return False

    def move_to_xyz(self, x: float, y: float, z: float, speed: int = 50) -> bool:
        return self.move_to(x, y, z, wait=True)

    def set_joints(self, angles: list, speed: int = 50) -> bool:
        try:
            logging.info(f"[DofbotRobot] 관절: {angles}")
            self.sio.emit('set_joints', {'joints': angles})
            return True
        except Exception as e:
            logging.error(f"[DofbotRobot] 관절 에러: {e}")
            return False

    def set_gripper(self, open_percent: float) -> bool:
        try:
            angle = 10 + (open_percent / 100.0) * 160
            self.sio.emit('set_gripper', {'gripper': int(angle)})
            return True
        except: return False

    def move_gripper(self, open_percent: float) -> bool:
        return self.set_gripper(open_percent)

    def set_force(self, force: float) -> bool:
        try:
            self.sio.emit('set_force', {'force': int(force*100)})
            return True
        except: return False

    def get_current_pose(self) -> dict:
        # 스로틀링 제거: 요청마다 바로 반환
        with self.state_lock:
            if not self.latest_state:
                return {"position": {"x":0,"y":0,"z":0}, "joints":[0]*5, "gripper":0, "is_moving":False}
            
            ee = self.latest_state.get('ee', {})
            return {
                "position": {
                    "x": ee.get('x', 0)*100.0,
                    "y": ee.get('y', 0)*100.0,
                    "z": ee.get('z', 0)*100.0
                },
                "joints": self.latest_state.get('joints', [0]*5),
                "gripper": 0, "is_moving": False
            }

    def get_current_position(self) -> Optional[Tuple[float, float, float]]:
        p = self.get_current_pose()["position"]
        return (p["x"], p["y"], p["z"])

    def emergency_stop(self):
        pass
