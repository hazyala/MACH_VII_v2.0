#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyBullet 서버 상태 확인

실제 물체 위치와 탐지된 좌표를 비교합니다.
"""

import requests
import json

SERVER_URL = "http://localhost:5000"

print("=" * 70)
print("PyBullet 서버 상태 확인")
print("=" * 70)

try:
    # 1. 서버 연결 확인
    print(f"\n[서버 연결 테스트]")
    response = requests.get(f"{SERVER_URL}/", timeout=2)
    print(f"  서버 상태: 연결됨")
    
except requests.exceptions.ConnectionError:
    print(f"  ❌ 서버에 연결할 수 없습니다.")
    print(f"  PyBullet 서버가 실행 중인지 확인하세요:")
    print(f"    cd d:\\ARMY\\MACH_VII_v2.0\\pubullet_source")
    print(f"    streamlit run app.py")
    exit(1)
except Exception as e:
    print(f"  오류: {e}")
    exit(1)

print(f"\n[물체 정보 확인 필요]")
print(f"  PyBullet Streamlit UI에서 물체 위치 확인:")
print(f"    1. 브라우저에서 http://localhost:8501 열기")
print(f"    2. 'Object Manager' 섹션에서 물체 위치 확인")
print(f"    3. Pos: (x, y, z) 값 확인")

print(f"\n[현재 탐지 결과]")
print(f"  로그 픽셀: (374, 237)")
print(f"  로그 depth: 0.5374m")
print(f"  계산된 좌표: (11.72, 7.65, 12.27)cm")

print(f"\n[검증 방법]")
print(f"  1. Streamlit UI에서 실제 물체 위치 확인")
print(f"  2. 물체 위치 = 계산된 좌표? → ✅ 정확")
print(f"  3. 물체 위치 ≠ 계산된 좌표? → ❌ 추가 디버깅 필요")

print(f"\n[예상 시나리오]")
print(f"  만약 물체가 실제로 (10, 10, 10.5)cm에 있다면:")
print(f"    - 예상 픽셀: (392, 237)")
print(f"    - 예상 depth: 0.5621m")
print(f"  ")
print(f"  현재 픽셀 (374, 237)은 약간 다릅니다.")
print(f"  → 물체가 다른 위치에 있거나, 카메라 파라미터 조정 필요")

print("\n" + "=" * 70)
