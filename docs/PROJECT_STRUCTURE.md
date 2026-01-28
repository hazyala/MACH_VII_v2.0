# 📁 MACH-VII v2.0 폴더 구조 및 파일 명세

이 문서는 프로젝트의 디렉토리 구조와 각 주요 파일의 역할을 정의합니다.
이 구조는 **Living Agent** 아키텍처(7 Layer Pipeline)를 그대로 반영하고 있습니다.

## 📦 전체 디렉토리 트리 (Target Architecture)

MACH_VII_v2.0/
├── 📂 sensor/               # [Layer 1] 감각 계층 (Raw Data)
│   ├── realsense_driver.py  # RealSense 카메라 드라이버
│   ├── vision_base.py       # 비전 인터페이스
│   └── pybullet_vision.py   # 시뮬레이션 비전
│
├── 📂 state/                # [Layer 2] 상태 계층 (Single Source of Truth)
│   ├── system_state.py      # 전체 시스템 상태 (Root Object)
│   └── emotion_state.py     # 감정 상태 컴포넌트
│
├── 📂 brain/                # [Layer 3] 판단 계층 (Decision/Intent)
│   ├── logic_brain.py       # 로직 기반 판단 모듈
│   └── emotion_updater.py   # LLM 기반 감정 업데이트
│
├── 📂 strategy/             # [Layer 4] 전략 계층 (Filtering/Mode)
│   ├── base_policy.py       # 행동 정책 인터페이스
│   ├── safe_policy.py       # 안전 모드 정책
│   └── explore_policy.py    # 탐험 모드 정책
│
├── 📂 expression/           # [Layer 5] 표현 계층 (Interpolation)
│   └── emotion_controller.py# 감정/표정 제어 및 보간 (60Hz)
│
├── 📂 embodiment/           # [Layer 6] 구현 계층 (Action/Rendering)
│   ├── 📂 frontend/         # React 웹 UI
│   └── 📂 hardware/         # 로봇 하드웨어 제어
│       ├── robot_base.py    # 로봇 인터페이스
│       └── dofbot_robot.py  # 실제 로봇 드라이버
│
├── 📂 memory/               # [Layer 7] 기억 계층 (DB)
│   ├── falkordb_manager.py  # Graph DB 관리자
│   └── 📂 data/             # [Persistence] DB 데이터 저장소 (Docker Volume)
│
├── 📂 shared/               # 공통 유틸리티
│   └── ...
│
├── 📂 interface/            # 외부 인터페이스
│   └── 📂 backend/
│       └── api_server.py    # FastAPI 백엔드 서버
│
├── main.py                  # [Root] 시스템 실행 진입점
├── docker-compose.yml       # [Conf] DB 컨테이너 설정
└── environment.yml          # [Conf] Conda 환경 설정

## 🔍 주요 디렉토리별 역할 상세

### 1. `sensor/`
*   **역할**: 하드웨어로부터 Raw Data를 수집합니다.
*   **주의**: 데이터를 해석하거나 가공하지 않고 상위 레이어로 전달만 합니다.

### 2. `state/`
*   **역할**: 수집된 데이터를 통합하여 "현재 상황"을 정의합니다.
*   **핵심 파일**: `system_state.py` (전체 시스템의 상태를 담는 객체)

### 3. `brain/`
*   **역할**: "무엇을 할 것인가"를 결정합니다.
*   **특징**: 하드웨어를 직접 제어하지 않고 `Intent`(의도)만 생성합니다.
❌ 포함되면 안 되는 것
모터 각도 계산
UI 상태 직접 변경
하드웨어 API 호출

### 4. `strategy/`
*   **역할**: Brain의 단기적 판단이 장기적 목표/성향에 위배되지 않는지 검사합니다.

### 5. `expression/`
*   **역할**: 추상적인 `Intent`를 구체적인 물리량(각도, 속도)으로 변환합니다.
*   **특징**: 60fps 루프가 돌아가며 부드러운 보간(Interpolation)을 수행합니다.

### 6. `embodiment/`
*   **역할**: 최종 물리량을 실제로 화면에 그리거나 모터를 움직입니다.
*   **규칙**: 자체적인 판단 로직을 절대 포함하지 않습니다. (UI is Dumb)

### 7. `shared/`
*   **역할**: 모든 레이어에서 공통으로 사용하는 설정값과 데이터 타입을 관리합니다.
*   **규칙**: 여기 있는 모듈은 어디서든 Import 가능하지만, 비즈니스 로직을 포함해선 안 됩니다.
