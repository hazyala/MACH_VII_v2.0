#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
V1.0 축 변환 테스트
"""

import sys
sys.path.append('.')

from sensor.projection import pybullet_projection

print("=" * 80)
print("V1.0 축 변환 테스트")
print("=" * 80)

pixel_x, pixel_y = 367, 276
depth_m = 0.5940

print(f"\n[입력]")
print(f"픽셀: ({pixel_x}, {pixel_y})")
print(f"Depth: {depth_m}m")

x_cm, y_cm, z_cm = pybullet_projection.pixel_to_3d(pixel_x, pixel_y, depth_m)

print(f"\n[결과]")
print(f"로봇 베이스 좌표: ({x_cm:.2f}, {y_cm:.2f}, {z_cm:.2f})cm")

print(f"\n[비교]")
print(f"예상 (PyBullet 실제): (10, 10, 2.5)cm")
print(f"계산 결과: ({x_cm:.2f}, {y_cm:.2f}, {z_cm:.2f})cm")

import math
error = math.sqrt((x_cm-10)**2 + (y_cm-10)**2 + (z_cm-2.5)**2)
print(f"총 오차: {error:.2f}cm")

if error < 5:
    print("✅ 양호 (5cm 이내)")
elif error < 10:
    print("⚠️ 개선 필요 (5-10cm)")
else:
    print("❌ 부정확 (10cm 초과)")

print("\n" + "=" * 80)
