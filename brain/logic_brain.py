import time
import uuid
from typing import Dict, Any
from shared.state_broadcaster import broadcaster
from .strategy_selector import StrategySelector
from memory.falkordb_manager import memory_manager

class LogicBrain:
    """
    메인 논리 에이전트 클래스입니다.
    """
    def __init__(self):
        self.selector = StrategySelector()
        self.context = {
            "allow_explore": False,
            "risk_level": "LOW"
        }

    def set_context(self, allow_explore: bool, risk_level: str):
        self.context["allow_explore"] = allow_explore
        self.context["risk_level"] = risk_level
        print(f"[LogicBrain] Context Updated: Explore={allow_explore}, Risk={risk_level}")

    def execute_task(self, task_command: str):
        episode_id = str(uuid.uuid4())
        start_time = time.time()
        
        # 1. 상태 업데이트 -> 계획 수립 (PLANNING)
        broadcaster.publish("agent_state", "PLANNING")
        time.sleep(1) # 계획 수립 시뮬레이션
        
        # 2. 상태 업데이트 -> 실행 중 (EXECUTING)
        broadcaster.publish("agent_state", "EXECUTING")
        broadcaster.publish("episode_result", "ongoing")
        
        # 3. 정책 선택
        # 메모리 사용을 위해 task_command 전달
        policy = self.selector.select_policy(self.context, task_command)
        print(f"[LogicBrain] Selected Policy: {type(policy).__name__}")
        
        # 메모리 기록을 위한 시작 감정 포착
        from expression.emotion_controller import emotion_controller
        start_emotion = emotion_controller.get_current_emotion()
        
        # 4. 실행 (Execute)
        target = {"x": 30.0, "y": 0.0, "z": 20.0}
        
        success = True
        if task_command == "task_fail":
            success = False
        else:
            success = policy.execute_move(target, self.context)
        
        # 5. 결과 및 메모리 저장
        end_emotion = emotion_controller.get_current_emotion()
        result_str = "success" if success else "failure"
        
        # 메모리 쓰기 트리거
        episode_data = {
            "id": episode_id,
            "timestamp": start_time,
            "result": result_str,
            "action": {"type": "move", "target": task_command},
            "start_emotion": start_emotion,
            "end_emotion": end_emotion
        }
        memory_manager.save_episode(episode_data)
        
        if success:
            broadcaster.publish("episode_result", "success")
            broadcaster.publish("agent_state", "SUCCESS")
            time.sleep(2) # 성공 표정 보여주기
            broadcaster.publish("agent_state", "IDLE")
        else:
            broadcaster.publish("episode_result", "failure")
            broadcaster.publish("agent_state", "RECOVERING")
            time.sleep(2) # 실패 표정 보여주기
            broadcaster.publish("agent_state", "IDLE")
            
# MVP 편의를 위한 싱글톤 객체
logic_brain = LogicBrain()