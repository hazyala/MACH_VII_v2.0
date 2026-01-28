# core/pybullet_robot.py

import requests
from embodiment.hardware.robot_base import RobotBase

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
            # 시뮬레이터 규격에 맞춰 cm를 m로 변환합니다 (100cm = 1m).
            pos_m = [x / 100.0, y / 100.0, z / 100.0]
            payload = {"pos": pos_m, "speed": speed}
            
            response = requests.post(f"{self.server_url}/set_pos", json=payload, timeout=2.0)
            
            if response.status_code == 200:
                # 내부 상태 정보에 현재 목표 위치를 저장합니다.
                self.current_state["position"] = {"x": x, "y": y, "z": z}
                return True
            return False
        except Exception:
            return False

    def move_gripper(self, open_percent: float) -> bool:
        """
        그리퍼의 개폐 정도를 제어합니다 (0: 닫힘, 100: 열림).
        """
        try:
            payload = {"open_percent": open_percent}
            response = requests.post(f"{self.server_url}/set_gripper", json=payload, timeout=2.0)
            
            if response.status_code == 200:
                self.current_state["gripper"] = open_percent
                return True
            return False
        except Exception:
            return False

    def get_current_pose(self) -> dict:
        """
        현재 로봇 손끝(End-effector)의 cm 좌표를 서버로부터 가져옵니다.
        """
        try:
            response = requests.get(f"{self.server_url}/get_pose", timeout=1.0)
            if response.status_code == 200:
                data = response.json()
                # m 단위를 다시 cm 단위로 변환하여 반환합니다.
                return {
                    "x": data["pos"][0] * 100.0,
                    "y": data["pos"][1] * 100.0,
                    "z": data["pos"][2] * 100.0
                }
        except Exception:
            pass
        return self.current_state["position"]