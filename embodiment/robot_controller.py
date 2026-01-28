import threading
import time
from typing import Dict, Any
from shared.state_broadcaster import broadcaster
from state.system_state import system_state
from .hardware.pybullet_robot import PybulletRobot

class RobotController:
    """
    Brain의 '의도(Intent)'를 물리적인 움직임으로 변환하는 싱글톤 컨트롤러입니다.
    Broadcaster의 'action_intent' 채널을 구독합니다.
    """
    def __init__(self):
        self.lock = threading.Lock()
        # 기본적으로 PyBullet 로봇 드라이버 사용 (추후 설정에 따라 변경 가능)
        self.robot_driver = PybulletRobot() 
        self.running = False
        self.last_intent = None
        
        # 구독 시작
        broadcaster.subscribe(self.on_intent_received)
        
    def start(self):
        self.running = True
        print("[RobotController] 하드웨어 제어기 시작됨.")

    def stop(self):
        self.running = False
        
    def on_intent_received(self, data: Any):
        """Broadcaster로부터 상태 스냅샷을 수신하여 의도 변화를 감지합니다."""
        if not isinstance(data, dict):
            return

        # 'action_intent' 키에서 의도 추출
        intent = data.get("action_intent")
        
        # 의도가 없거나 이전과 동일하면 무시
        if not intent or intent == self.last_intent:
            return
            
        print(f"[RobotController] 새 의도 감지: {intent}")
        self.last_intent = intent
        system_state.robot.is_moving = True
        
        # 비차단 실행을 위해 스레드로 실행
        threading.Thread(target=self._execute, args=(intent,), daemon=True).start()

    def _execute(self, intent: str):
        try:
            intent_low = intent.lower()
            print(f"[RobotController] '{intent}' 수행 시작...")
            
            # 2. 잡기 (Pick-up) 동작
            if any(k in intent_low for k in ["잡아", "집어", "pick", "grab", "연"]):
                perception = system_state.perception_data
                objects = perception.get("detected_objects", [])
                
                if not objects:
                    broadcaster.publish("agent_thought", "[Robot] 시야에 물체가 보이지 않아 제자리 대기합니다.")
                    return
                
                target_obj = objects[0]
                label = target_obj.get("label", "Object")
                broadcaster.publish("agent_thought", f"[Robot] '{label}' 근처로 팔을 뻗습니다.")
                
                # PyBullet 데모 좌표 (나중에 perception 데이터 기반으로 보정 필요)
                self.robot_driver.move_to_xyz(15, 0, 5) 
                time.sleep(1.0)
                self.robot_driver.move_gripper(100) # 열기
                time.sleep(0.5)
                self.robot_driver.move_to_xyz(15, 0, 2) # 접근
                time.sleep(0.5)
                self.robot_driver.move_gripper(0) # 닫기
                time.sleep(1.0)
                self.robot_driver.move_to_xyz(15, 0, 15) # 들어올리기
                broadcaster.publish("agent_thought", f"[Robot] '{label}'을(를) 집어 올렸습니다.")

            # 3. 인사 (Greet) 동작
            elif any(k in intent_low for k in ["인사", "반가워", "hello", "greet", "안녕"]):
                broadcaster.publish("agent_thought", "[Robot] 팔을 흔들어 인사합니다.")
                for _ in range(2):
                    self.robot_driver.move_to_xyz(25, 5, 30)
                    time.sleep(0.4)
                    self.robot_driver.move_to_xyz(25, -5, 30)
                    time.sleep(0.4)
                self.robot_driver.move_to_xyz(25, 0, 30)
                
            # 4. 정지 (Stop)
            elif any(k in intent_low for k in ["멈춰", "정지", "stop"]):
                self.robot_driver.emergency_stop()
                broadcaster.publish("agent_thought", "[Robot] 동작을 즉시 중단했습니다.")

            # 5. 기타 이동
            elif "이동" in intent_low or "move" in intent_low:
                broadcaster.publish("agent_thought", "[Robot] 지정된 위치로 이동을 수행합니다.")
                self.robot_driver.move_to_xyz(20, 0, 20)
            
            else:
                broadcaster.publish("agent_thought", f"[Robot] '{intent}'에 해당하는 동작을 정의할 수 없어 보류합니다.")

        except Exception as e:
            print(f"[RobotController] 오류: {e}")
            broadcaster.publish("agent_thought", f"[Robot] 실행 중 예기치 못한 오류 발생: {str(e)}")
        finally:
            system_state.robot.is_moving = False
            broadcaster.publish("agent_thought", "[Robot] 행동 시퀀스 종료.")

# 싱글톤
robot_controller = RobotController()
