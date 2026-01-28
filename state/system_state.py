from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from .emotion_state import EmotionVector

@dataclass
class RobotStatus:
    is_moving: bool = False
    battery_level: float = 100.0
    current_mode: str = "IDLE"

@dataclass
class SystemState:
    """
    시스템의 전체 상태를 정의하는 Single Source of Truth입니다.
    Brain은 이 객체를 보고 판단을 내립니다.
    """
    # 하위 상태 컴포넌트들
    emotion: EmotionVector = field(default_factory=EmotionVector)
    robot: RobotStatus = field(default_factory=RobotStatus)
    
    # 센서 데이터 (Raw Data가 아닌 가공된 정보)
    perception_data: Dict[str, Any] = field(default_factory=dict)
    
    # 현재 활성화된 Intent (Brain이 결정한 의도)
    current_intent: str = "IDLE"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "emotion": self.emotion.to_dict(),
            "robot": {
                "is_moving": self.robot.is_moving,
                "battery": self.robot.battery_level,
                "mode": self.robot.current_mode
            },
            "perception": self.perception_data,
            "intent": self.current_intent
        }

# 전역 상태 인스턴스 (메모리상 유일)
system_state = SystemState()
