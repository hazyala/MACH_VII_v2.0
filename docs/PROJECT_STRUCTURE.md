# 📁 MACH-VII v2.0 폴더 구조 및 파일 명세

이 문서는 프로젝트의 디렉토리 구조와 각 주요 파일의 역할을 정의합니다.
이 구조는 **Living Agent** 아키텍처(7 Layer Pipeline)를 그대로 반영하고 있습니다.

## 📦 전체 디렉토리 트리 (Target Architecture)

```
MACH_VII_v2.0/
├── 📂 sensor/               # [Layer 1] 감각 계층 (Input)
│   ├── realsense_driver.py  # RealSense 카메라 제어 드라이버
│   └── mic_input.py         # 마이크 입력 처리
│
├── 📂 state/                # [Layer 2] 상태 계층 (State Definition)
│   ├── world_model.py       # 현재 환경 모델링
│   └── system_state.py      # 시스템 상태 정의 (DTO)
│
├── 📂 brain/                # [Layer 3] 판단 계층 (Decision Making)
│   ├── logic_brain.py       # 메인 로직 결정 (LLM/Rule)
│   └── emotion_core.py      # 감정 상태 관리
│
├── 📂 strategy/             # [Layer 4] 전략 계층 (Filtering)
│   ├── mode_manager.py      # Safe/Explore/Combat 모드 관리
│   └── personality.py       # 성향 필터
│
├── 📂 expression/           # [Layer 5] 표현 계층 (Physics Interaction)
│   ├── expression_engine.py # 60fps 움직임 보간 및 생성
│   └── motion_library.py    # 사전 정의된 모션(인사, 거절 등)
│
├── 📂 embodiment/           # [Layer 6] 구현 계층 (Rendering/Hardware)
│   ├── 📂 frontend/         # React 기반 얼굴 UI (Websocket Client)
│   └── 📂 hardware/         # 실제 로봇 하드웨어 드라이버 (Dofbot 등)
│
├── 📂 memory/               # [Layer 7] 기억 계층 (Storage)
│   ├── falkordb_manager.py  # Graph DB 연동
│   └── logger.py            # 시스템 로그 관리
│
├── 📂 shared/               # 공통 모듈 (Cross-cutting Concerns)
│   ├── config.py            # 전역 설정
│   ├── event_bus.py         # 내부 메시지 브로드캐스터
│   └── types.py             # 공용 데이터 타입 (DTO)
│
├── 📂 docs/                 # 프로젝트 문서 (인수인계용)
│   ├── PROJECT_STRUCTURE.md # 본 파일
│   ├── RUN_GUIDE.md         # 실행 가이드
│   └── ARCHITECTURE_GUIDELINES.md # 설계 원칙
│
├── .gitignore               # Git 무시 설정
├── environment.yml          # Conda 환경 설정 파일
└── main.py                  # 프로그램 진입점 (Entry Point)
```

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
