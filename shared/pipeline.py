# shared/pipeline.py

import threading
import time
from typing import Dict, Any, List, Optional
from shared.state_broadcaster import broadcaster
from state.system_state import system_state
from strategy.strategy_manager import strategy_manager

class SystemPipeline:
    """
    7-레이어 아키텍처의 단방향 데이터 흐름을 오케스트레이션하는 클래스입니다.
    Sensor -> State -> Brain -> Strategy -> Expression -> Embodiment -> Memory
    순서로 데이터가 흐르도록 제어합니다.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SystemPipeline, cls).__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self):
        self.running = False
        self.components = {} # 각 레이어의 핸들러 등록 공간

    def register_component(self, name: str, component: Any):
        """레이어별 컴포넌트를 등록합니다."""
        self.components[name] = component
        print(f"[Pipeline] 컴포넌트 등록됨: {name}")

    def process_brain_intent(self, intent: str):
        """
        Brain에서 결정된 의도(Intent)를 파이프라인의 후속 단계로 흘려보냅니다.
        Brain (Layer 3) -> Strategy (Layer 4) -> Expression (Layer 5) -> Embodiment (Layer 6) -> Memory (Layer 7)
        """
        print(f"\n[Pipeline] === 파이프라인 실행 시작 (Intent: {intent}) ===")
        
        # 1. Strategy Filtering (Layer 4)
        if not strategy_manager.filter_action(intent):
            print(f"[Pipeline] [Layer 4: Strategy] 행동이 차단되었습니다: {intent}")
            broadcaster.publish("agent_thought", f"[Strategy] 현재 전략 모드에서 차단된 행동입니다: {intent}")
            return

        # 2. Expression / Emotion Mapping (Layer 5)
        # 의도에 따른 감정 상태 변화 유도 (예: '인사' -> confidence 증가)
        if "인사" in intent or "hello" in intent:
             self.components.get("emotion_controller").update_target({"confidence": 0.2})
        
        # 3. Embodiment Execution (Layer 6)
        # 로봇 제어기에 의도 전달 (Broadcaster를 통해 간접 전달하던 방식을 파이프라인이 정교하게 제어 가능)
        system_state.current_intent = intent
        broadcaster.publish("action_intent", intent)
        
        # 4. Memory Archiving (Layer 7)
        # 최종 결정과 실행 결과를 메모리에 기록 (추후 구현 예정)
        print(f"[Pipeline] [Layer 7: Memory] 실행 로그 기록 중: {intent}")
        
        print("[Pipeline] === 파이프라인 실행 완료 ===\n")

    def get_system_snapshot(self) -> Dict[str, Any]:
        """
        단방향 흐름에 따라 수집된 전체 시스템 상태의 정합성 있는 스냅샷을 반환합니다.
        UI 스트리밍 등에 사용됩니다.
        """
        # 1. Sensor & State 단계의 데이터를 최신화하여 가져옴
        return {
            "brain": broadcaster.get_snapshot(),
            "emotion": self.components.get("emotion_controller").get_current_emotion(),
            "perception": system_state.perception_data,
            "robot": system_state.robot,
            "strategy": strategy_manager.get_context(),
            "timestamp": time.time()
        }

# 싱글톤 인스턴스
pipeline = SystemPipeline()
