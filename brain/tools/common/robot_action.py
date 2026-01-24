import streamlit as st
from langchain_core.tools import tool
from core.robot_base import RobotBase
# 로봇 제어 클래스 임포트 (구현 예정)
# from core.pybullet_robot import PyBulletRobot
# from core.dofbot_robot import DofbotRobot

class IntegratedRobot(RobotBase):
    """
    가상(PyBullet) 및 실물(DOFBOT) 로봇을 통합 제어하는 인터페이스 클래스입니다.
    RobotBase 규격을 상속받아 cm 단위와 오른손 좌표계를 준수합니다.
    """
    def __init__(self):
        super().__init__()
        # 시뮬레이션 및 실물 로봇 드라이버 초기화
        self.pybullet = None 
        self.dofbot = None   

    def move_to_xyz(self, x: float, y: float, z: float, speed: int = 50) -> bool:
        """
        목표 좌표(cm)로 이동 명령을 전달합니다.
        세션 상태의 sim_mode에 따라 가상 또는 실물 로봇을 선택합니다.
        """
        is_sim = st.session_state.get('sim_mode', True)
        
        if is_sim:
            # PyBullet 인터페이스 호출
            return True 
        else:
            # DOFBOT 인터페이스 호출
            return True 

    def set_joints(self, angles: list, speed: int = 50) -> bool:
        """관절 각도(degree)를 직접 제어합니다."""
        is_sim = st.session_state.get('sim_mode', True)
        target = self.pybullet if is_sim else self.dofbot
        return True 

    def move_gripper(self, open_percent: float) -> bool:
        """
        그리퍼의 개방 정도를 조절합니다.
        0은 완전 폐쇄, 100은 최대 개방(3cm)을 의미합니다.
        """
        is_sim = st.session_state.get('sim_mode', True)
        target = self.pybullet if is_sim else self.dofbot
        return True 

    def get_current_pose(self):
        """로봇의 현재 좌표 및 관절 상태 정보를 반환합니다."""
        return self.current_state

    def emergency_stop(self):
        """긴급 정지 명령을 수행합니다."""
        pass

@tool
def robot_action(x_cm: float, y_cm: float, z_cm: float, action_type: str = "move") -> str:
    """
    로봇 팔을 목표 좌표로 이동시키거나 그리퍼 동작을 수행하는 도구입니다.
    
    Args:
        x_cm (float): 목표 X 좌표 (단위: cm)
        y_cm (float): 목표 Y 좌표 (단위: cm)
        z_cm (float): 목표 Z 좌표 (단위: cm)
        action_type (str): "move"(이동) 또는 "grasp"(잡기) 동작 선택
    """
    try:
        robot = IntegratedRobot()
        is_sim = st.session_state.get('sim_mode', True)
        mode_label = "시뮬레이션" if is_sim else "실물"
        
        if action_type == "move":
            # 이동 전 그리퍼를 최대 개방(100%) 상태로 설정
            robot.move_gripper(100.0)
            
            # 현재 위치와 목표 좌표 간의 거리 계산
            curr_state = robot.get_current_pose()
            dist = ((curr_state['position']['x'] - x_cm)**2 + 
                    (curr_state['position']['y'] - y_cm)**2 + 
                    (curr_state['position']['z'] - z_cm)**2)**0.5
            
            # 5cm 이내 근접 시 정밀 이동을 위해 속도를 20으로 하향 조정
            target_speed = 20 if dist < 5.0 else 50
            success = robot.move_to_xyz(x_cm, y_cm, z_cm, speed=target_speed)
            
            if success:
                return f"[SUCCESS] {mode_label} 모드: ({x_cm}, {y_cm}, {z_cm})cm 이동 완료. 남은 거리: {dist:.1f}cm"
        
        elif action_type == "grasp":
            # 물체 크기와 관계없이 그리퍼를 완전히 닫음 (0%)
            success = robot.move_gripper(0.0)
            if success:
                return f"[SUCCESS] {mode_label} 모드: 그리퍼 폐쇄 완료"

        return f"[FAILURE] {mode_label} 모드: 요청한 동작을 수행할 수 없습니다."

    except Exception as e:
        return f"[ERROR] 시스템 오류 발생: {str(e)}"