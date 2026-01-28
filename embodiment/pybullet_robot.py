# embodiment/pybullet_robot.py

from .robot_base import RobotBase
from interface.pybullet_client import pybullet_client

class PybulletRobot(RobotBase):
    """
    파이불렛 시뮬레이터와 통신하여 로봇을 제어하는 실제 구현 클래스입니다.
    """
    def __init__(self, server_url="http://localhost:5000"):
        super().__init__()
        self.server_url = server_url

    def move_to_xyz(self, x: float, y: float, z: float, speed: int = 50) -> bool:
        """
        cm 단위 좌표를 받아 서버에 이동 명령을 보냅니다.
        """
        try:
            # cm를 m로 변환하여 전송
            pos_m = [x / 100.0, y / 100.0, z / 100.0]
            pybullet_client.set_pos(pos_m)
            self.current_state["position"] = {"x": x, "y": y, "z": z}
            return True
        except Exception:
            return False

    def move_gripper(self, open_percent: float) -> bool:
        """
        그리퍼의 개폐 정도를 제어합니다 (0: 닫힘, 100: 열림).
        """
        try:
            # open_percent(0~100) -> 0.0 ~ 0.06 m 변환
            # PyBullet 규격: 0.0(닫힘), 0.06(최대 열림)
            val = (open_percent / 100.0) * 0.06
            pybullet_client.set_gripper(val)
            self.current_state["gripper"] = open_percent
            return True
        except Exception:
            return False

    def get_current_pose(self) -> dict:
        """
        현재 로봇 손끝(End-effector)의 cm 좌표를 서버로부터 가져옵니다.
        """
        # pybullet_client가 실시간 수신하는 최신 상태 반환
        state = pybullet_client.latest_state.get('robot', {})
        pos = state.get('ee', {})
        return {
            "x": pos.get('x', 0) * 100.0,
            "y": pos.get('y', 0) * 100.0,
            "z": pos.get('z', 0) * 100.0
        }

    def set_joints(self, angles: list, speed: int = 50) -> bool:
        """
        5개 관절의 각도를 직접 제어합니다.
        """
        try:
            pybullet_client.set_joints(angles)
            self.current_state["joints"] = angles
            return True
        except Exception:
            return False

    def emergency_stop(self):
        """
        위급 상황 시 로봇의 모든 구동을 즉시 중단합니다.
        """
        try:
            self.current_state["is_moving"] = False
            requests.post(f"{self.server_url}/stop", timeout=1.0)
        except Exception:
            pass