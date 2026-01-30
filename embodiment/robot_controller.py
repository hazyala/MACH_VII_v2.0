import threading
import time
import queue
from typing import Dict, Any, Optional
from shared.state_broadcaster import broadcaster
from state.system_state import system_state
from .robot_factory import RobotFactory

class RobotController:
    """
    Brain의 '의도(Intent)'를 물리적인 움직임으로 변환하는 싱글톤 컨트롤러입니다.
    동작 큐(Action Queue)를 사용하여 명령의 순차적 실행을 보장합니다.
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.robot_driver = RobotFactory.get_robot()
        self.running = False
        self.last_intent = None
        
        # 동작 큐 및 워커 스레드 설정
        self.action_queue = queue.Queue()
        self.worker_thread: Optional[threading.Thread] = None
        
        # 구독 시작
        broadcaster.subscribe(self.on_intent_received)
        
    def switch_robot(self, target: str):
        """실시간으로 제어 대상 로봇을 전환합니다 (pybullet / dofbot)"""
        from shared.config import GlobalConfig
        from shared.ui_dto import RobotTarget
        
        with self.lock:
            # 설정 값 업데이트
            GlobalConfig.SIM_MODE = (target == RobotTarget.VIRTUAL)
            # 신규 드라이버 획득
            self.robot_driver = RobotFactory.get_robot()
            
        print(f"[RobotController] 로봇 전환 완료: {target} (SIM_MODE={GlobalConfig.SIM_MODE})")
        
    def start(self):
        if self.running: return
        self.running = True
        
        # 워커 스레드 시작
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        
        print("[RobotController] 하드웨어 제어기 및 워커 루프 시작됨.")

    def stop(self):
        self.running = False
        if self.worker_thread:
            # 큐에 None을 넣어 워커 종료 유도 (선택 사항)
            self.action_queue.put(None)
            self.worker_thread.join(timeout=1.0)
        
    def on_intent_received(self, data: Any):
        """Broadcaster로부터 상태 스냅샷을 수신하여 의도를 큐에 적재합니다."""
        if not isinstance(data, dict) or not self.running:
            return

        intent = data.get("action_intent")
        
        # 의도가 없거나 이전과 동일하면 대기 (중복 명령 방어)
        if not intent or intent == self.last_intent:
            return
            
        print(f"[RobotController] 새 의도 수신 (큐 적재): {intent}")
        self.last_intent = intent
        
        # 큐에 명령 추가
        self.action_queue.put(intent)

    def _worker_loop(self):
        """큐에서 명령을 하나씩 꺼내어 순차적으로 실행하는 메인 루프"""
        while self.running:
            try:
                # 0.5초 대기하며 큐 확인
                intent = self.action_queue.get(timeout=0.5)
                if intent is None: break # 종료 신호
                
                # 실제 동작 수행
                self._execute(intent)
                
                # 큐 작업 완료 표시
                self.action_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[RobotController] 워커 루프 예외: {e}")

    def _execute(self, intent: str):
        try:
            system_state.robot.is_moving = True
            intent_low = intent.lower()
            print(f"[RobotController] '{intent}' 수행 시작 (큐 처리 중)...")
            
            # 2. 잡기 (Pick-up) 동작
            if any(k in intent_low for k in ["잡아", "집어", "pick", "grab"]):
                perception = system_state.perception_data
                objects = perception.get("detected_objects", [])
                
                if not objects:
                    broadcaster.publish("agent_thought", "[Robot] 시야에 물체가 없어 제자리 대기합니다.")
                else:
                    target_obj = objects[0]
                    label = target_obj.get("label", "Object")
                    broadcaster.publish("agent_thought", f"[Robot] '{label}' 물체 조작을 시작합니다.")
                    
                    self.robot_driver.move_to_xyz(15, 0, 5) 
                    time.sleep(1.0)
                    self.robot_driver.move_gripper(100)
                    time.sleep(0.5)
                    self.robot_driver.move_to_xyz(15, 0, 2)
                    time.sleep(0.5)
                    self.robot_driver.move_gripper(0)
                    time.sleep(1.0)
                    self.robot_driver.move_to_xyz(15, 0, 15)
                    broadcaster.publish("agent_thought", f"[Robot] '{label}' 조작 완료.")

            # 3. 인사 (Greet) 동작
            elif any(k in intent_low for k in ["인사", "반가워", "hello", "greet", "안녕"]):
                broadcaster.publish("agent_thought", "[Robot] 인사를 수행합니다.")
                for _ in range(2):
                    self.robot_driver.move_to_xyz(25, 5, 30)
                    time.sleep(0.4)
                    self.robot_driver.move_to_xyz(25, -5, 30)
                    time.sleep(0.4)
                self.robot_driver.move_to_xyz(25, 0, 30)
                
            # 4. 정지 (Stop)
            elif any(k in intent_low for k in ["멈춰", "정지", "stop"]):
                # 정지는 큐를 비워야 할 수도 있지만, 일단 즉시 정지 명령만 하달
                self.robot_driver.emergency_stop()
                broadcaster.publish("agent_thought", "[Robot] 긴급 정지 실행.")

            # 5. 기타 이동
            elif "이동" in intent_low or "move" in intent_low:
                broadcaster.publish("agent_thought", "[Robot] 위치 이동 중...")
                self.robot_driver.move_to_xyz(20, 0, 20)
            
            else:
                broadcaster.publish("agent_thought", f"[Robot] '{intent}' 동작 보류 (미정의).")

        except Exception as e:
            print(f"[RobotController] 실행 오류: {e}")
            broadcaster.publish("agent_thought", f"[Robot] 오류 발생: {str(e)}")
        finally:
            system_state.robot.is_moving = False
            broadcaster.publish("agent_thought", "[Robot] 동작 완료.")
            # 동작 간 최소 간격 (안정화)
            time.sleep(0.5)

# 싱글톤
robot_controller = RobotController()

# 싱글톤
robot_controller = RobotController()
