import threading
import time
from typing import Dict, Any, List, Callable

class StateBroadcaster:
    """
    LogicBrain이 상태를 발행하고 감정 시스템/UI가 이를 구독할 때 사용하는 싱글톤 브로드캐스터입니다.
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(StateBroadcaster, cls).__new__(cls)
                    cls._instance._init()
        return cls._instance
    
    def _init(self):
        self.subscribers: List[Callable[[Dict[str, Any]], None]] = []
        self.latest_state = {
            "agent_state": "IDLE",     # PLANNING, EXECUTING, RECOVERING, IDLE
            "object_type": "none",     # 컵, 공 등
            "episode_result": "none",  # 성공(success), 실패(failure)
            "robot_status": "ok",      # 정상(ok), 오류(error)
            "timestamp": time.time()
        }
    
    def subscribe(self, callback: Callable[[Dict[str, Any]], None]):
        """상태 업데이트를 수신할 콜백 함수를 등록합니다."""
        with self._lock:
            self.subscribers.append(callback)
            
    def publish(self, key: str, value: Any):
        """특정 상태 키를 업데이트하고 구독자들에게 알립니다."""
        with self._lock:
            self.latest_state[key] = value
            self.latest_state["timestamp"] = time.time()
            snapshot = self.latest_state.copy()
            
        # 구독자들에게 알림 (이상적으로는 비동기여야 하지만 MVP를 위해 단순 루프 사용)
        for sub in self.subscribers:
            try:
                sub(snapshot)
            except Exception as e:
                print(f"[Broadcaster] 구독자 오류: {e}")

    def get_snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return self.latest_state.copy()

# 전역 인스턴스
broadcaster = StateBroadcaster()
