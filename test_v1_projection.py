#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
V1.0 방식 좌표 변환 테스트
"""

import sys
sys.path.append('.')

from sensor.projection import pybullet_projection

print("=" * 80)
print("V1.0 방식 좌표 변환 테스트")
print("=" * 80)

# 로그에서 나온 값
pixel_x, pixel_y = 367, 276
depth_buffer = 0.5940

print(f"\n[입력]")
print(f"픽셀: ({pixel_x}, {pixel_y})")
print(f"Depth buffer: {depth_buffer}")

x_cm, y_cm, z_cm = pybullet_projection.pixel_to_3d(pixel_x, pixel_y, depth_buffer)

print(f"\n[결과]")
print(f"로봇 베이스 좌표: ({x_cm:.2f}, {y_cm:.2f}, {z_cm:.2f})cm")

print(f"\n[비교]")
print(f"예상 (PyBullet 실제): (10, 10, 2.5)cm")
print(f"V1.0 계산 결과: ({x_cm:.2f}, {y_cm:.2f}, {z_cm:.2f})cm")

import math
error = math.sqrt((x_cm-10)**2 + (y_cm-10)**2 + (z_cm-2.5)**2)
print(f"총 오차: {error:.2f}cm")

if error < 5:
    print("✅ 양호 (5cm 이내)")
else:
    print("❌ 부정확 (5cm 초과)")

print("\n" + "=" * 80)
