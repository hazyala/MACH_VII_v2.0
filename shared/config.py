import os
from pathlib import Path
from dotenv import load_dotenv

# 1. 프로젝트 전역 설정
class GlobalConfig:
    """
    시스템의 동작 모드와 주요 서버 정보를 관리합니다.
    """
    # True: 파이불렛 시뮬레이션 모드, False: 실물 로봇 모드
    SIM_MODE = True
    
    # VLM(Gemma3) 분석 서버 주소 및 모델 명칭
    VLM_ENDPOINT = "http://ollama.aikopo.net/api/generate"
    VLM_MODEL = "gemma3:27b"

# 2. 카메라 오프셋 설정 (cm 단위)
class CameraConfig:
    """
    로봇 베이스(0, 0, 0) 기준 카메라의 위치 오프셋입니다.
    """
    # 파이불렛 시뮬레이션 설정 (1.0m -> 100cm)
    SIM_OFFSET = {
        "x": 100.0,
        "y": 0.0,
        "z": 100.0
    }

    # 실물 리얼센스 카메라 설정
    REAL_OFFSET = {
        "x": 0.0,
        "y": 0.0,
        "z": 0.0
    }

# 3. 경로 관리 (OS 독립적 Pathlib 사용)
# shared 폴더의 부모인 프로젝트 루트 경로를 설정합니다.
BASE_DIR = Path(__file__).resolve().parent.parent

# 주요 레이어 디렉토리 경로
CORE_DIR = BASE_DIR / "core"
BRAIN_DIR = BASE_DIR / "brain"
INTERFACE_DIR = BASE_DIR / "interface"
SHARED_DIR = BASE_DIR / "shared"
DATA_DIR = BASE_DIR / "base_data" # 충돌 방지를 위해 명칭을 조정할 수 있습니다.

# [중요] Brain 하위의 모듈(Logic) 경로 추가
MODULES_DIR = BRAIN_DIR / "modules"
VISION_MODULE_DIR = MODULES_DIR / "vision"
ROBOT_MODULE_DIR = MODULES_DIR / "robot"

# Tools 경로
TOOLS_DIR = BRAIN_DIR / "tools"
VISION_TOOL_DIR = TOOLS_DIR / "vision"
COMMON_TOOL_DIR = TOOLS_DIR / "common"

# 데이터 및 모델 에셋 경로
MODEL_DIR = DATA_DIR / "models"
ASSET_DIR = DATA_DIR / "assets"
LOG_DIR = DATA_DIR / "logs"

# YOLO 모델 파일 절대 경로
VISION_MODEL_PATH = MODEL_DIR / "yolo11s.pt"

# 4. 환경 변수 로드
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

def init_system_dirs():
    """
    시스템 가동에 필수적인 데이터 및 모듈 폴더가 없을 경우 생성합니다.
    소스 코드 폴더(modules, tools)는 수동 생성을 권장하나, 안전을 위해 체크합니다.
    """
    # 생성 혹은 확인이 필요한 주요 디렉토리 목록
    target_dirs = [
        DATA_DIR, MODEL_DIR, ASSET_DIR, LOG_DIR,
        MODULES_DIR, VISION_MODULE_DIR, ROBOT_MODULE_DIR,
        TOOLS_DIR, VISION_TOOL_DIR, COMMON_TOOL_DIR
    ]
    
    for directory in target_dirs:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)

# 모듈 로드 시 즉시 폴더 구조를 점검합니다.
init_system_dirs()