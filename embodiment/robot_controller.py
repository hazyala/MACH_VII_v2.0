import threading
import time
import queue
from typing import Dict, Any, Optional
from shared.state_broadcaster import broadcaster
from state.system_state import system_state
from .robot_factory import RobotFactory
from strategy.visual_servoing import visual_servoing

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
        
        # 동기 실행 모드 (True: 에이전트가 블로킹됨 / False: 비동기 큐 처리)
        self.SYNC_EXECUTION = True
        
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
        
        # 워커 스레드 시작 (비동기 모드일 때만 유효하지만, 하이브리드를 위해 유지)
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        
        print("[RobotController] 하드웨어 제어기 및 워커 루프 시작됨.")
        # [Force] 초기 구동력 최대 설정 (물리 엔진 버티기 방지)
        self.robot_driver.set_force(500)

    def stop(self):
        self.running = False
        if self.worker_thread:
            # 큐에 None을 넣어 워커 종료 유도 (선택 사항)
            self.action_queue.put(None)
            self.worker_thread.join(timeout=1.0)
        
    def on_intent_received(self, data: Any):
        """Broadcaster로부터 상태 스냅샷을 수신하여 의도를 큐에 적재하거나 즉시 실행합니다."""
        if not isinstance(data, dict) or not self.running:
            return

        # 1. 기존 action_intent 처리
        intent = data.get("action_intent")
        if intent and intent != self.last_intent:
            print(f"[RobotController] 새 의도 수신: {intent}")
            self.last_intent = intent
            
            if self.SYNC_EXECUTION:
                # [동기 실행] 에이전트(Broadcaster) 스레드에서 직접 실행
                self._execute(intent)
            else:
                self.action_queue.put(("action", intent))
        
        # 2. grasp_intent 처리 (중복 방지)
        grasp_intent_data = data.get("grasp_intent")
        if grasp_intent_data:
            # 동일한 grasp_intent 중복 체크
            intent_id = f"{grasp_intent_data['target_name']}_{grasp_intent_data.get('timestamp', '')}" 
            if not hasattr(self, 'last_grasp_intent') or self.last_grasp_intent != intent_id:
                print(f"[RobotController] Grasp 의도 수신: {grasp_intent_data['target_name']}")
                self.last_grasp_intent = intent_id
                
                if self.SYNC_EXECUTION:
                     # [동기 실행]
                    self._execute_grasp(grasp_intent_data)
                else:
                    self.action_queue.put(("grasp", grasp_intent_data))

    def _worker_loop(self):
        """큐에서 명령을 하나씩 꺼내어 순차적으로 실행하는 메인 루프"""
        while self.running:
            try:
                # 0.5초 대기하며 큐 확인
                item = self.action_queue.get(timeout=0.5)
                if item is None: break # 종료 신호
                
                intent_type, intent_data = item
                
                # 실제 동작 수행
                if intent_type == "action":
                    self._execute(intent_data)
                elif intent_type == "grasp":
                    self._execute_grasp(intent_data)
                
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
                    
                    # 5단계 비주얼 서보잉 위임 (Async Lock은 visual_servoing 내부에서 처리)
                    success = visual_servoing.execute_pick_sequence(
                        target_label=label,
                        get_ee_position=self.robot_driver.get_current_pose,
                        move_robot=self.robot_driver.move_to_xyz,
                        move_gripper=self.robot_driver.move_gripper
                    )
                    
                    if success:
                         broadcaster.publish("agent_thought", f"[Robot] '{label}' 조작 성공.")
                    else:
                         broadcaster.publish("agent_thought", f"[Robot] '{label}' 조작 실패.")

            # 3. 인사 (Greet) 동작
            elif any(k in intent_low for k in ["인사", "반가워", "hello", "greet", "안녕"]):
                broadcaster.publish("agent_thought", "[Robot] 인사를 수행합니다.")
                for _ in range(2):
                    self.robot_driver.move_to_xyz(25, 5, 30)
                    time.sleep(0.4)
                    self.robot_driver.move_to_xyz(25, -5, 30)
                    time.sleep(0.4)
                self.robot_driver.move_to_xyz(25, 0, 30)
                
            # 4. 정지 (Stop) - 최우선 처리
            elif any(k in intent_low for k in ["멈춰", "정지", "stop"]):
                logging.warning("[RobotController] 🛑 긴급 정지 명령 수신!")
                
                # 1. visual_servoing 즉시 중단
                visual_servoing.stop()
                
                # 2. 로봇 긴급 정지
                self.robot_driver.emergency_stop()
                
                # 3. 대기 중인 모든 명령 제거
                with self.action_queue.mutex:
                    self.action_queue.queue.clear()
                
                # 4. 상태 초기화
                self.last_intent = None
                if hasattr(self, 'last_grasp_intent'):
                    self.last_grasp_intent = None
                    
                broadcaster.publish("agent_thought", "[Robot] 🛑 긴급 정지 완료 (큐 초기화)")
                logging.info("[RobotController] 긴급 정지 완료")

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

    def _execute_grasp(self, intent_data: dict):
        """
        Grasp Intent를 받아 visual_servoing을 실행합니다.
        Strategy Layer에서 전달된 정밀한 파지 명령을 처리합니다.
        """
        try:
            system_state.robot.is_moving = True
            
            target_name = intent_data["target_name"]
            grasp_pose = intent_data["grasp_pose"]
            
            broadcaster.publish("agent_thought", 
                              f"[Robot] '{target_name}' 물체 잡기를 시작합니다.")
            
            # 그리퍼 개방
            self.robot_driver.move_gripper(grasp_pose['gripper_width'])
            
            # 비주얼 서보잉 실행
            success = visual_servoing.execute_pick_sequence(
                target_label=target_name,
                get_ee_position=self.robot_driver.get_current_pose,
                move_robot=self.robot_driver.move_to_xyz,
                move_gripper=self.robot_driver.move_gripper,
                get_gripper_ratio=getattr(self.robot_driver, 'get_gripper_ratio', None),
                grasp_offset_z=grasp_pose.get('grasp_depth_offset', 0.0)
            )
            
            
            if success:
                broadcaster.publish("agent_thought", 
                                  f"[Robot] '{target_name}' 파지 시퀀스 완료! "
                                  f"⚠️ 반드시 vision_analyze 툴로 파지 성공 여부를 검증해주세요!")
            else:
                broadcaster.publish("agent_thought", f"[Robot] '{target_name}' 조작 실패.")
                
        except Exception as e:
            print(f"[RobotController] Grasp 실행 오류: {e}")
            broadcaster.publish("agent_thought", f"[Robot] 오류 발생: {str(e)}")
        finally:
            system_state.robot.is_moving = False
            broadcaster.publish("agent_thought", "[Robot] 동작 완료.")
            time.sleep(0.5)

# 싱글톤
robot_controller = RobotController()
