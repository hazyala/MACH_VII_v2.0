# brain/tools/common/robot_action.py

from langchain_core.tools import tool
from brain.modules.robot.robot_factory import RobotFactory
from brain.modules.robot.motion_controller import MotionController

@tool
def robot_action(x_cm: float, y_cm: float, z_cm: float, action_type: str = "move") -> str:
    """
    로봇 팔을 특정 cm 좌표로 이동하거나 물체를 잡는 동작을 수행합니다.
    목표 좌표와 현재 위치를 실시간으로 대조하여 정밀 제어를 실행합니다.
    """
    try:
        # 1. 공장을 통해 현재 모드에 맞는 로봇 획득
        robot = RobotFactory.get_robot()
        controller = MotionController()
        
        if not robot:
            return "[FAILURE] 로봇 시스템을 초기화할 수 없습니다."

        # 2. 현재 위치 확인 및 이동 전략 수립
        current_pose = robot.get_current_pose()
        target_pose = {"x": x_cm, "y": y_cm, "z": z_cm}
        strategy = controller.get_strategy(current_pose, target_pose)

        # 3. 명령 수행
        if action_type == "move":
            # 이동 전 그리퍼를 열어 충돌을 방지합니다.
            robot.move_gripper(100.0)
            
            # 전략에 따른 속도로 이동 명령 전송
            success = robot.move_to_xyz(x_cm, y_cm, z_cm, speed=strategy["speed"])
            
            if success:
                return f"[SUCCESS] {strategy['msg']} 완료 (거리: {strategy['distance']:.2f}cm)"
            return "[FAILURE] 로봇 이동 명령이 거부되었습니다."

        elif action_type == "grasp":
            # 물체를 잡기 위해 그리퍼를 완전히 닫습니다.
            if robot.move_gripper(0.0):
                return "[SUCCESS] 그리퍼 폐쇄 및 파지 완료"
            return "[FAILURE] 그리퍼 제어에 실패했습니다."

        return "[FAILURE] 정의되지 않은 작업 타입입니다."

    except Exception as e:
        return f"[ERROR] 로봇 동작 중 시스템 오류 발생: {str(e)}"