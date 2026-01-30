# YOLO 모델 업그레이드 가이드

## 현재 상태
- 모델: YOLOv11s (small)
- 정확도: 낮음 (곰 인형을 "kite"로 오탐지)
- 추론 속도: 빠름

## 권장 업그레이드
YOLOv11x (extra-large) 또는 YOLOv11l (large)로 업그레이드

### 1. 모델 다운로드
```bash
# YOLOv11x (최고 정확도, 느림)
cd d:\ARMY\MACH_VII_v2.0\data\models
wget https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11x.pt

# 또는 YOLOv11l (중간 정확도, 적당한 속도)
wget https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11l.pt
```

Windows PowerShell에서:
```powershell
cd d:\ARMY\MACH_VII_v2.0\data\models
Invoke-WebRequest -Uri "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11x.pt" -OutFile "yolo11x.pt"
```

### 2. 코드 수정
`sensor/yolo_detector.py` 수정:

```python
def __init__(self, model_path: str = None):
    if model_path is None:
        # yolo11s.pt → yolo11x.pt 또는 yolo11l.pt
        model_path = str(PathConfig.MODEL_DIR / "yolo11x.pt")
```

### 3. 성능 비교

| 모델      | mAP   | 속도 (FPS) | 크기   |
|-----------|-------|-----------|--------|
| YOLOv11s  | ~45%  | ~150      | 10MB   |
| YOLOv11m  | ~50%  | ~100      | 25MB   |
| YOLOv11l  | ~53%  | ~70       | 50MB   |
| YOLOv11x  | ~55%  | ~50       | 100MB  |

## 즉시 적용 방법

1. 모델 다운로드 (위의 PowerShell 명령 사용)
2. `sensor/yolo_detector.py` 14번 라인 수정
3. 서버 재시작

더 나은 탐지 정확도를 원하면 **yolo11x.pt** 권장!
