# brain/modules/robot/robot_factory.py

import streamlit as st
from embodiment.hardware.pybullet_robot import PybulletRobot

class RobotFactory:
    """
    설정에 맞는 로봇 드라이버 인스턴스를 생성하여 반환합니다.
    """
    @staticmethod
    def get_robot():
        # Streamlit 세션 상태에서 시뮬레이션 여부를 확인합니다.
        is_sim = st.session_state.get("sim_mode", True)
        
        if is_sim:
            return PybulletRobot()
        
        # 향후 실물 로봇(DofbotRobot) 추가 시 이 부분에 구현체를 연결합니다.
        return None