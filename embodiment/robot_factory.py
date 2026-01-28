# embodiment/robot_factory.py

from shared.config import GlobalConfig
from .pybullet_robot import PybulletRobot

class RobotFactory:
    """
    전역 설정(SIM_MODE)에 맞는 로봇 드라이버 인스턴스를 생성하여 반환합니다.
    """
    _instance = None

    @staticmethod
    def get_robot():
        """
        설정된 모드에 따라 로봇 드라이버를 반환합니다.
        싱글톤 패턴을 적용하여 중복 생성을 방지할 수 있습니다.
        """
        if GlobalConfig.SIM_MODE:
            return PybulletRobot()
        
        # 실물 로봇(Dofbot) 드라이버는 향후 구현 시 추가
        # return DofbotRobot()
        return None