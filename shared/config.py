import os
from pathlib import Path
from dotenv import load_dotenv

class GlobalConfig:
    """시스템 전역 설정 클래스입니다."""
    SIM_MODE = True
    
    # 브레인(Brain) 설정
    LLM_ENDPOINT = "http://ollama.aikopo.net/api/generate"
    LLM_MODEL = "gemma3:27b"
    
    # 감정(Emotion) 설정
    EMOTION_UPDATE_INTERVAL = 0.5  # 초 단위 (저수준 LLM 업데이트 주기)
    EMOTION_RENDER_FPS = 60        # 초당 프레임 수 (고수준 보간 루프)
    
    # 로봇(Robot) 설정
    ROBOT_IP = "192.168.0.100"     # DOFBOT IP 주소
    
class PathConfig:
    """pathlib을 사용한 경로 관리 클래스입니다."""
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    CORE_DIR = BASE_DIR / "core"
    BRAIN_DIR = BASE_DIR / "brain"
    EMOTION_DIR = BASE_DIR / "emotion"
    POLICY_DIR = BASE_DIR / "policy"
    MEMORY_DIR = BASE_DIR / "memory"
    INTERFACE_DIR = BASE_DIR / "interface"
    SHARED_DIR = BASE_DIR / "shared"
    
    DATA_DIR = BASE_DIR / "base_data"
    MODEL_DIR = DATA_DIR / "models"
    LOG_DIR = DATA_DIR / "logs"

    @staticmethod
    def ensure_dirs():
        for path in [PathConfig.DATA_DIR, PathConfig.MODEL_DIR, PathConfig.LOG_DIR]:
            path.mkdir(parents=True, exist_ok=True)

# 환경 변수 로드
load_dotenv(PathConfig.BASE_DIR / ".env")
PathConfig.ensure_dirs()