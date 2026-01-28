import time
import threading
from shared.state_broadcaster import broadcaster
from expression.emotion_controller import emotion_controller

class LLMUpdater:
    """
    축적된 컨텍스트를 기반으로 LLM(Gemma3)에게 감정 목표 조정을 요청하는
    저빈도(Low-rate) 루프입니다.
    """
    def __init__(self):
        self.running = False
        
    def start(self):
        self.running = True
        thread = threading.Thread(target=self._loop, daemon=True)
        thread.start()
        
    def _loop(self):
        print("[Emotion-LLM] 업데이터 시작됨 (Low-rate).")
        idle_start_time = 0
        
        while self.running:
            # 저빈도: 2초마다 실행
            time.sleep(2.0)
            
            # 컨텍스트 획득
            context = broadcaster.get_snapshot()
            agent_state = context.get("agent_state", "IDLE")
            
            # 휴리스틱 로직 (LLM 추론 시뮬레이션)
            updates = {}
            
            # 1. 지루함 메커니즘 (너무 오래 IDLE 상태인 경우)
            if agent_state == "IDLE":
                if idle_start_time == 0:
                    idle_start_time = time.time()
                elif time.time() - idle_start_time > 10.0:
                    # 지루함 -> 호기심 증가
                    # print("[Emotion-LLM] 에이전트가 지루해합니다. 호기심을 증가시킵니다.")
                    updates["curiosity"] = 0.8
            else:
                idle_start_time = 0
                
            # 2. 자신감 확인 (성공/실패 여부)
            episode_result = context.get("episode_result", "none")
            if episode_result == "success":
                updates["confidence"] = 0.9
            elif episode_result == "failure":
                updates["confidence"] = 0.2
                
            # 업데이트가 있으면 적용
            if updates:
                emotion_controller.update_target(updates)

# 싱글톤
llm_updater = LLMUpdater()
