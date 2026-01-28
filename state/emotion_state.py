from dataclasses import dataclass, field, asdict
from typing import Dict

@dataclass
class EmotionVector:
    """
    연속적인 5차원 감정 벡터입니다.
    범위: 0.0 ~ 1.0 (클램핑됨).
    """
    focus: float = 0.5       # 주의 집중도 (Idle -> Hyped)
    effort: float = 0.0      # 신체적/정신적 부하
    confidence: float = 0.5  # 자신감
    frustration: float = 0.0 # 오류/실패 누적
    curiosity: float = 0.5   # 탐험 욕구

    def update(self, delta: Dict[str, float]):
        """델타 업데이트를 안전하게 적용합니다."""
        for key, value in delta.items():
            if hasattr(self, key):
                current = getattr(self, key)
                new_val = max(0.0, min(1.0, current + value))
                setattr(self, key, new_val)
    
    def to_dict(self):
        return asdict(self)
