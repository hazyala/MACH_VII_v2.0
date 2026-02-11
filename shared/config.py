import os
from pathlib import Path
from dotenv import load_dotenv # 환경 변수 로드용

class GlobalConfig:
    """시스템 전역 설정 클래스입니다."""
    SIM_MODE = False # 현재 시스템이 시뮬레이션(PyBullet) 모드인지, 실제 로봇 모드인지 결정하는 스위치
    
    # 브레인(Brain) 설정
    VLM_ENDPOINT = "http://ollama.aikopo.net/api/generate" # 엔드포인트를 통해 호출할 모델 주소
    VLM_MODEL = "gemma3:27b" # 엔드포인트를 통해 호출할 모델 이름
    
    # PyBullet 서버 설정 (포트 충돌 방지를 위해 5001로 변경)
    # DOFBOT 서버가 포트 5000을 사용하므로 PyBullet은 5001을 사용합니다
    PYBULLET_HOST = "localhost"
    PYBULLET_PORT = 5001
    SIM_SERVER_URL = f"http://{PYBULLET_HOST}:{PYBULLET_PORT}"
    
    # DOFBOT 서버 설정 (클라이언트로 연결)
    # DOFBOT_ROBOT_ARM-main/main.py 서버와 통신합니다
    DOFBOT_SERVER_HOST = "192.168.25.100"  # 실제 DOFBOT이 다른 PC에 있다면 해당 IP로 변경
    DOFBOT_SERVER_PORT = 5000
    DOFBOT_SERVER_URL = f"http://{DOFBOT_SERVER_HOST}:{DOFBOT_SERVER_PORT}"
    
    # API 서버 포트
    API_PORT = 8000
    
    # 감정(Emotion) 설정
    EMOTION_UPDATE_INTERVAL = 0.5  # 초 단위 (저수준 LLM 업데이트 주기)
    EMOTION_RENDER_FPS = 60        # 초당 프레임 수 (고수준 보간 루프로 60fps)
    
    # RealSense 카메라 설정
    REALSENSE_ENABLE_GRIPPER_CAM = True  # 그리퍼 카메라 활성화 여부
    REALSENSE_ENABLE_IMU = True  # IMU(가속도/자이로) 데이터 활성화 여부
    CAMERA_FPS = 30 # 카메라 FPS
    
    # 레거시 호환성 (기존 코드와의 호환을 위해 유지)
    ROBOT_IP = DOFBOT_SERVER_URL  # 기존 ROBOT_IP를 DOFBOT_SERVER_URL로 매핑 

class CameraConfig:
    """카메라 설치 위치 및 오프셋 설정 클래스입니다."""
    # 시뮬레이션 환경 (PyBullet) 오프셋
    # PyBullet 카메라 위치: cameraEyePosition=[0.5, 0, 0.5] (m 단위)
    # → cm 단위로 변환: X=50cm, Y=0cm, Z=50cm
    SIM_OFFSET = {"x": 50.0, "y": 0.0, "z": 50.0}  # cm 단위
    
    # 실물 환경 (Intel RealSense) 오프셋 
    REAL_OFFSET = {"x": 63.0, "y": 0.0, "z": 54.0} #(일단 자로 재긴 했는데 정확함은 나중에 확인 필요) cm 단위
    
class PathConfig:
    """pathlib을 사용한 경로 관리 클래스입니다."""
    # pathlib 사용 이유는, 전역 관리가 쉽기 때문 (하드코딩 방지)
   
    # __file__ : 현재 파일의 경로를 나타냄
    # resolve() : 상대 경로를 절대 경로로 변환
    # parent : 상위 디렉토리
    # parent.parent : 상위 디렉토리의 상위 디렉토리
    # / : pathlib의 경로 연결 연산자
    # mkdir() : 디렉토리 생성
    # parents=True : 상위 디렉토리가 없으면 생성
    # exist_ok=True : 디렉토리가 이미 있으면 무시
    # ensure_dirs() : 필요 디렉토리가 없으면 생성

    # BASE_DIR : 프로젝트의 최상위 디렉토리
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    # 7 Layer Pipeline 및 주요 디렉토리
    SENSOR_DIR = BASE_DIR / "sensor"
    STATE_DIR = BASE_DIR / "state"
    BRAIN_DIR = BASE_DIR / "brain"
    STRATEGY_DIR = BASE_DIR / "strategy"
    EXPRESSION_DIR = BASE_DIR / "expression"
    EMBODIMENT_DIR = BASE_DIR / "embodiment"
    MEMORY_DIR = BASE_DIR / "memory"
    
    # 공유 및 인터페이스
    SHARED_DIR = BASE_DIR / "shared"
    INTERFACE_DIR = BASE_DIR / "interface"
    
    # 데이터 및 문서
    DATA_DIR = BASE_DIR / "data"
    MODEL_DIR = DATA_DIR / "models"
    LOG_DIR = DATA_DIR / "logs"
    DOCS_DIR = BASE_DIR / "docs"

    @staticmethod
    def ensure_dirs():
        """필요한 데이터 디렉토리가 없으면 생성합니다."""
        for path in [PathConfig.DATA_DIR, PathConfig.MODEL_DIR, PathConfig.LOG_DIR]:
            path.mkdir(parents=True, exist_ok=True)

# 환경 변수 로드 
# .env 파일에서 환경 변수를 로드할 수도 있으니까 미리 만들어둠. (.env.example로 만들어둠 내용은 없음)
load_dotenv(PathConfig.BASE_DIR / ".env")
PathConfig.ensure_dirs()