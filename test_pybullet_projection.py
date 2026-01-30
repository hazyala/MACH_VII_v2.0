#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyBullet projection 단위 테스트

알려진 물체 위치에 대해 역투영이 정확한지 검증합니다.
"""

import sys
sys.path.append('.')

import numpy as np
from sensor.projection import pybullet_projection

print("=" * 80)
print("PyBullet Projection 단위 테스트")
print("=" * 80)

# PyBullet 실제 설정
print("\n[테스트 설정]")
print("물체 위치: (0.1, 0.1, 0.025)m = (10, 10, 2.5)cm")
print("카메라 위치: (0.5, 0, 0.5)m")
print("픽셀: (367, 276)")
print("Depth: 0.5940")

# 테스트 호출
pixel_x, pixel_y = 367, 276
depth_buffer = 0.5940

try:
    x_cm, y_cm, z_cm = pybullet_projection.pixel_to_3d(pixel_x, pixel_y, depth_buffer)
    
    print(f"\n[역투영 결과]")
    print(f"월드 좌표: ({x_cm:.2f}, {y_cm:.2f}, {z_cm:.2f})cm")
    
    # 예상값과 비교
    expected_x, expected_y, expected_z = 10.0, 10.0, 2.5
    error_x = abs(x_cm - expected_x)
    error_y = abs(y_cm - expected_y)
    error_z = abs(z_cm - expected_z)
    
    print(f"\n[오차 분석]")
    print(f"X 오차: {error_x:.2f}cm")
    print(f"Y 오차: {error_y:.2f}cm")
    print(f"Z 오차: {error_z:.2f}cm")
    
    total_error = np.sqrt(error_x**2 + error_y**2 + error_z**2)
    print(f"총 오차: {total_error:.2f}cm")
    
    if total_error < 2.0:
        print(f"\n✅ 테스트 성공! (허용 오차 2cm 이내)")
    else:
        print(f"\n❌ 테스트 실패! (오차가 2cm를 초과함)")
        
except Exception as e:
    print(f"\n❌ 에러 발생: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
