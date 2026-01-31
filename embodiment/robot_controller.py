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
        # [CRITICAL] 긴급 정지 처리를 위해 반드시 False로 설정해야 합니다.
        # 동기 실행 모드 (True: 에이전트가 블로킹됨 / False: 비동기 큐 처리)
        # [CRITICAL] 긴급 정지 처리를 위해 반드시 False로 설정해야 합니다.
        self.SYNC_EXECUTION = False
        
        # [Safety] 사용자 수동 정지 시 자율 행동 잠금 플래그
        self.safety_lock = False
        
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
            
    def _handle_emergency_stop(self):
        """긴급 정지 로직 (즉시 실행)"""
        import logging
        logging.warning("[RobotController] 🛑 긴급 정지 명령 수신 (Immediate)!")
        
        # 1. visual_servoing 즉시 중단
        visual_servoing.stop()
        
        # 2. 로봇 긴급 정지
        self.robot_driver.emergency_stop()
        
        # 3. 대기 중인 모든 명령 제거
        with self.action_queue.mutex:
            self.action_queue.queue.clear()
        
        broadcaster.publish("agent_thought", "[Robot] 🛑 긴급 정지 완료 (큐 초기화)")
        logging.info("[RobotController] 긴급 정지 완료")
        
        # [Safety] 안전 잠금 활성화 - Brain의 자동 재시도 무시
        self.safety_lock = True
        broadcaster.publish("agent_thought", "[Safety] 🔒 안전 장치 작동: '재개' 명령 전까지 자율 행동이 차단됩니다.")
        
    def on_intent_received(self, data: Any):
        """Broadcaster로부터 상태 스냅샷을 수신하여 의도를 큐에 적재하거나 즉시 실행합니다."""
        if not isinstance(data, dict) or not self.running:
            return

        # 1. 기존 action_intent 처리
        intent = data.get("action_intent")
        if intent:
            # 1. 중복 의도 필터링 (Stop 포함 모든 의도에 적용)
            if intent != self.last_intent:
                self.last_intent = intent
                
                intent_lower = intent.lower()
                
                # [CRITICAL] 정지 명령은 큐를 거치지 않고 즉시 실행 (Priority Interrupt)
                if any(k in intent_lower for k in ["멈춰", "정지", "stop"]):
                    self._handle_emergency_stop()
                    return
                
                # [Safety] 안전 잠금 확인
                if self.safety_lock:
                    # 잠금 해제 키워드 확인
                    if any(k in intent_lower for k in ["재개", "resume", "풀어", "unlock"]):
                        self.safety_lock = False
                        broadcaster.publish("agent_thought", "[Safety] 🔓 안전 장치 해제. 작업을 재개합니다.")
                        logging.info("[Safety] 잠금 해제")
                    else:
                        logging.warning(f"[Safety] 🔒 잠금 상태! '{intent}' 명령무시.")
                        broadcaster.publish("agent_thought", f"[Safety] 🔒 정지 상태입니다. 재개하려면 '재개'라고 말해주세요.")
                        return

                print(f"[RobotController] 새 의도 수신: {intent}")
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
                    broadcaster.publish("agent_thought", f"[Robot] '{label}' 물체 조작(접근+파지)을 시작합니다.")
                    
                    # 5단계 비주얼 서보잉 위임 (Async Lock은 visual_servoing 내부에서 처리)
                    # [Refactor] execute_pick_sequence -> execute_approach_and_grasp
                    success = visual_servoing.execute_approach_and_grasp(
                        target_label=label,
                        get_ee_position=self.robot_driver.get_current_pose,
                        move_robot=self.robot_driver.move_to_xyz,
                        move_gripper=self.robot_driver.move_gripper
                    )
                    
                    if success:
                         broadcaster.publish("agent_thought", f"[Robot] '{label}' 파지 완료. 다음 행동을 지시해주세요 (예: 들어올려).")
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
            
            # [New] 들어올리기 (Lift) 동작 - Agent 주도 제어
            elif any(k in intent_low for k in ["들어올려", "lift", "올려"]):
                broadcaster.publish("agent_thought", "[Robot] 물체를 들어올립니다 (Lift).")
                current_pose = self.robot_driver.get_current_pose()
                target_z = current_pose['z'] + 15.0 # 15cm 상승
                
                success = self.robot_driver.move_to_xyz(
                    current_pose['x'], current_pose['y'], target_z, 
                    speed=40, wait_arrival=True
                )
                if success:
                    broadcaster.publish("agent_thought", "[Robot] 들어올리기 완료.")
                else:
                     broadcaster.publish("agent_thought", "[Robot] 들어올리기 실패.")

            # [Primtive] 상대 좌표 이동 (Relative Move)
            # 예: "왼쪽으로 10cm", "위로 조금", "move(x=10, y=0, z=0)"
            elif self._handle_relative_move(intent_low):
                pass # 핸들러 내부에서 처리됨

            # [Primitive] 그리퍼 제어 (Gripper Control)
            # 예: "그리퍼 열어", "박수", "gripper(0)"
            elif self._handle_primitive_gripper(intent_low):
                pass # 핸들러 내부에서 처리됨
                
            # 4. 정지 (Stop) - 최우선 처리 (on_intent_received에서 이미 처리됨)
            elif any(k in intent_low for k in ["멈춰", "정지", "stop"]):
                # 큐를 타고 들어온 경우에도 처리 (혹시 모를 대비)
                self._handle_emergency_stop()

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
            
            # 비주얼 서보잉 실행 (접근+파지)
            success = visual_servoing.execute_approach_and_grasp(
                target_label=target_name,
                get_ee_position=self.robot_driver.get_current_pose,
                move_robot=self.robot_driver.move_to_xyz,
                move_gripper=self.robot_driver.move_gripper,
                get_gripper_ratio=getattr(self.robot_driver, 'get_gripper_ratio', None),
                grasp_offset_z=grasp_pose.get('grasp_depth_offset', 0.0)
            )
            
            
            if success:
                broadcaster.publish("agent_thought", 
                                  f"[Robot] '{target_name}' 파지 완료! "
                                  f"⚠️ 반드시 vision_analyze 툴로 파지 성공 여부를 검증한 뒤, 'Lift' 명령을 내려주세요!")
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
    def _handle_relative_move(self, intent: str) -> bool:
        """
        상대 좌표 이동 명령을 파싱하고 실행합니다.
        Returns: 처리 여부 (True면 처리됨)
        """
        import re
        
        dx, dy, dz = 0.0, 0.0, 0.0
        processed = False
        speed = 40
        
        # 1. 자연어 키워드 매핑
        if "왼쪽" in intent or "left" in intent:
            dy = 5.0; processed = True
        if "오른쪽" in intent or "right" in intent:
            dy = -5.0; processed = True
        if "위" in intent or "up" in intent:
            dz = 5.0; processed = True
        if "아래" in intent or "down" in intent:
            dz = -5.0; processed = True
        if "앞" in intent or "front" in intent:
            dx = 5.0; processed = True
        if "뒤" in intent or "back" in intent:
            dx = -5.0; processed = True
            
        # 2. 수치 추출 (cm)
        amount_match = re.search(r'(\d+(?:\.\d+)?)', intent)
        if amount_match:
            val = float(amount_match.group(1))
            val = min(20.0, max(1.0, val)) # 안전 제한
            
            # (단순화) 발견된 방향 축에 값 적용
            if dx != 0: dx = val if dx > 0 else -val
            if dy != 0: dy = val if dy > 0 else -val
            if dz != 0: dz = val if dz > 0 else -val
        
        # 3. 함수형 커맨드 파싱: move(x=10, y=-5)
        func_match = re.search(r'move\((.*?)\)', intent)
        if func_match:
            try:
                params = func_match.group(1).split(',')
                for p in params:
                    if '=' not in p: continue
                    k, v = p.split('=')
                    k = k.strip().lower()
                    v = float(v.strip())
                    if k in ['x', 'dx']: dx = v
                    elif k in ['y', 'dy']: dy = v
                    elif k in ['z', 'dz']: dz = v
                processed = True
            except Exception as e:
                print(f"[RobotController] Move 파싱 오류: {e}")
        
        if not processed:
            return False
            
        broadcaster.publish("agent_thought", f"[Robot] 상대 이동: dx={dx}, dy={dy}, dz={dz}")
        cur = self.robot_driver.get_current_pose()
        return self.robot_driver.move_to_xyz(cur['x']+dx, cur['y']+dy, cur['z']+dz, speed=speed, wait_arrival=True)

    def _handle_primitive_gripper(self, intent: str) -> bool:
        """
        그리퍼 제어 명령을 파싱하고 실행합니다.
        Returns: 처리 여부
        """
        processed = False
        val = None # 0~100 (0:Close, 100:Open)
        
        # 1. 키워드
        if any(k in intent for k in ["열어", "open"]):
            val = 100; processed = True
        elif any(k in intent for k in ["잡아", "닫아", "close", "쥐어"]): 
            val = 0; processed = True
        elif any(k in intent for k in ["박수", "clap", "짝짝"]):
            broadcaster.publish("agent_thought", "[Robot] 박수를 칩니다 👏👏")
            for _ in range(3):
                self.robot_driver.move_gripper(100); time.sleep(0.15)
                self.robot_driver.move_gripper(0); time.sleep(0.15)
            self.robot_driver.move_gripper(50) 
            return True
            
        # 2. 함수형: gripper(50)
        import re
        func_match = re.search(r'gripper\((-?\d+)\)', intent)
        if func_match:
            val = float(func_match.group(1))
            processed = True
            
        if not processed or val is None:
            return False
            
        val = max(0, min(100, val))
        broadcaster.publish("agent_thought", f"[Robot] 그리퍼 제어: {val}%")
        return self.robot_driver.move_gripper(val)

# 싱글톤
robot_controller = RobotController()


