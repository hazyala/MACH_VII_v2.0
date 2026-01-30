# embodiment/pybullet_robot.py

import logging
from .robot_base import RobotBase
from interface.sim_client import pybullet_client

class PybulletRobot(RobotBase):
    """
    파이불렛 시뮬레이터와 통신하여 로봇을 제어하는 실제 구현 클래스입니다.
    """
    def __init__(self, server_url="http://localhost:5000"):
        super().__init__()
        self.server_url = server_url

    def move_to_xyz(self, x: float, y: float, z: float, speed: int = 50) -> bool:
        """
        로봇 베이스 기준 cm 좌표를 받아 PyBullet에 m 단위로 전송합니다.
        
        Args:
            x, y, z: 로봇 베이스 좌표계의 cm 단위 좌표
            speed: 이동 속도 (0~100)
        """
        try:
            # cm → m 변환
            pos_m = [x / 100.0, y / 100.0, z / 100.0]
            
            logging.info(f"[PybulletRobot] 이동 명령: ({x:.1f}, {y:.1f}, {z:.1f})cm "
                        f"→ PyBullet: ({pos_m[0]:.3f}, {pos_m[1]:.3f}, {pos_m[2]:.3f})m @ speed={speed}")
            
            # WebSocket으로 명령 전송
            pybullet_client.set_pos(pos_m)
            
            # 상태 업데이트
            self.current_state["position"] = {"x": x, "y": y, "z": z}
            
            logging.debug(f"[PybulletRobot] WebSocket 전송 완료 - connected: {pybullet_client.connected}")
            return True
        except Exception as e:
            logging.error(f"[PybulletRobot] 이동 실패: {e}")
            import traceback
            logging.error(traceback.format_exc())
            return False

    def move_gripper(self, open_percent: float) -> bool:
        """
        그리퍼의 개폐 정도를 제어합니다 (0: 닫힘, 100: 열림).
        """
        try:
            # open_percent(0~100) -> 0.0 ~ 0.06 m 변환
            # PyBullet 규격: 0.0(닫힘), 0.06(최대 열림)
            val = (open_percent / 100.0) * 0.06
            logging.info(f"[PybulletRobot] 그리퍼 동작: {open_percent:.1f}% ({'열림' if open_percent > 50 else '닫힘'})")
            pybullet_client.set_gripper(val)
            self.current_state["gripper"] = open_percent
            return True
        except Exception as e:
            logging.error(f"[PybulletRobot] 그리퍼 동작 실패: {e}")
            return False

    def get_current_pose(self) -> dict:
        """
        현재 로봇 손끝(End-effector)의 cm 좌표를 PyBullet 서버로부터 가져옵니다.
        """
        # pybullet_client가 실시간 수신하는 최신 상태 반환
        with pybullet_client.lock:
            state = pybullet_client.latest_state.get('robot', {})
        
        pos = state.get('ee', {})
        
        # m → cm 변환
        result = {
            "x": pos.get('x', 0) * 100.0,
            "y": pos.get('y', 0) * 100.0,
            "z": pos.get('z', 0) * 100.0
        }
        
        logging.info(f"[PybulletRobot] get_current_pose: PyBullet=({pos.get('x', 0):.3f}, "
                    f"{pos.get('y', 0):.3f}, {pos.get('z', 0):.3f})m "
                    f"→ ({result['x']:.1f}, {result['y']:.1f}, {result['z']:.1f})cm")
        return result

    def set_joints(self, angles: list, speed: int = 50) -> bool:
        """
        5개 관절의 각도를 직접 제어합니다.
        """
        try:
            logging.info(f"[PybulletRobot] 관절 각도 설정: {[f'{a:.1f}°' for a in angles]} @ speed={speed}")
            pybullet_client.set_joints(angles)
            self.current_state["joints"] = angles
            return True
        except Exception as e:
            logging.error(f"[PybulletRobot] 관절 제어 실패: {e}")
            return False

    def emergency_stop(self):
        """
        위급 상황 시 로봇의 모든 구동을 즉시 중단합니다.
        """
        logging.warning("[PybulletRobot] ⚠️  긴급 정지 발동!")
        try:
            self.current_state["is_moving"] = False
            # 실제 정지 명령은 pybullet_client를 통해 구현 가능
        except Exception as e:
            logging.error(f"[PybulletRobot] 긴급 정지 실패: {e}")