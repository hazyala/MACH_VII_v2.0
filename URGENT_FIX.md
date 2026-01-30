# 긴급 수정 사항

## 문제
1. **로그가 출력되지 않음** - `main.py`에 로깅 설정 없음
2. **좌표가 변하지 않음** - Python 캐시 문제 가능성
3. **로봇이 움직이지 않음** - 좌표 오류로 인한 정체

## 수정 완료

### 1. main.py에 로깅 설정 추가 ✅
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
```

### 2. Python 캐시 삭제 ✅
```powershell
Remove-Item -Recurse -Force .\__pycache__, .\sensor\__pycache__, ...
```

### 3. 수정된 파일 목록
- `main.py`: 로깅 설정 추가
- `sensor/pybullet_vision.py`: cx = 300 (수정)
- `sensor/vision_bridge.py`: 상세 로그 추가
- `sensor/vision_base.py`: pixel_to_cm 로그 추가

## 다음 단계

**서버를 재시작하면**:
1. 로그가 정상 출력됨
2. cx=300 적용됨
3. 캐시 문제 해결됨

**예상 로그 출력**:
```
INFO:root:[VisionBridge] 물체 #0 'sports ball': 픽셀=(350, 250), depth=0.7071m
INFO:root:[VisionBridge] 물체 #0 'sports ball': 카메라좌표=(...) + 오프셋(50, 0, 50) → 로봇베이스=(...)
```

**좌표 예상값**: (10, 10, 2.5)cm 근처로 수정될 것!
