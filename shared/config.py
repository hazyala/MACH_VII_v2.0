import os
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트의 최상위 루트 경로를 설정합니다. (shared 폴더의 부모 폴더)
# OS에 상관없이 절대 경로를 추적하여 경로 오류를 방지합니다.
BASE_DIR = Path(__file__).resolve().parent.parent

# 시스템의 주요 레이어 디렉토리 경로
CORE_DIR = BASE_DIR / "core"
BRAIN_DIR = BASE_DIR / "brain"
INTERFACE_DIR = BASE_DIR / "interface"
SHARED_DIR = BASE_DIR / "shared"
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = BASE_DIR / "docs"

# 데이터 및 에셋 세부 경로
MODEL_DIR = DATA_DIR / "models"
ASSET_DIR = DATA_DIR / "assets"
LOG_DIR = DATA_DIR / "logs"

# 사용할 YOLO 모델의 경로
VISION_MODEL_PATH = MODEL_DIR / "yolo11s.pt"

# 환경 변수 로드 (.env 파일이 존재할 경우 로드함)
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    # .env가 없을 경우 .env.example을 참고하라는 경고를 띄울 수 있습니다.
    pass

def init_system_dirs():
    """
    시스템 가동에 필수적인 데이터 관련 디렉토리가 없을 경우 생성합니다.
    """
    required_dirs = [DATA_DIR, MODEL_DIR, ASSET_DIR, LOG_DIR]
    for directory in required_dirs:
        directory.mkdir(parents=True, exist_ok=True)

# 모듈 로드 시 기본적으로 디렉토리 존재 여부를 확인합니다.
init_system_dirs()