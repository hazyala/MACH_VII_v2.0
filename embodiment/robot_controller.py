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
        self.lock = threading.RLock()
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
                
                # [Refactoring] ActionDispatcher가 직접 함수를 호출하므로
                # 큐 시스템을 거치지 않고 직접 실행되는 경우가 많으나,
                # 비동기 명령이 큐로 들어올 경우를 대비해 기본 골격은 유지
                if intent_type == "action":
                    self._execute(intent_data)
                
                self.action_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[RobotController] 워커 루프 예외: {e}")

    def _execute(self, intent: str):
        """
        [Legacy Support] 큐를 통해 들어온 문자열 명령 처리
        이제 대부분의 로직은 ActionDispatcher에서 처리되므로,
        이 함수는 legacy 문자열 명령에 대한 최소한의 호환성만 제공합니다.
        """
        try:
            system_state.robot.is_moving = True
            print(f"[RobotController] 큐 명령 실행: {intent}")
            # ... 필요한 경우 추가 구현, 현재는 로깅만
            
        except Exception as e:
            print(f"[RobotController] 실행 오류: {e}")
        finally:
            system_state.robot.is_moving = False



# 싱글톤
robot_controller = RobotController()


