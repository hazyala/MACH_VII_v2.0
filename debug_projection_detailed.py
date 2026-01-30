#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyBullet Projection 디버깅

NDC → World 변환의 각 단계를 출력하여 문제를 찾습니다.
"""

import sys
sys.path.append('.')

import numpy as np
from sensor.projection import pybullet_projection

# 강제로 상세 로그 출력
import logging
logging.basicConfig(level=logging.DEBUG, format='%(message)s')

print("=" * 80)
print("PyBullet Projection 상세 디버깅")
print("=" * 80)

# 로그에서 나온 값
pixel_x, pixel_y = 367, 276
depth_buffer = 0.5940

print(f"\n[입력값]")
print(f"픽셀: ({pixel_x}, {pixel_y})")
print(f"Depth buffer: {depth_buffer}")

# View/Projection matrix 가져오기
view_matrix, proj_matrix = pybullet_projection.get_matrices()

print(f"\n[View Matrix]")
print(view_matrix)

print(f"\n[Projection Matrix]")
print(proj_matrix)

# 수동으로 각 단계 계산
WIDTH = 600
HEIGHT = 480
near = 0.01
far = 10.0

# 1. Z-buffer → depth
depth_m = far * near / (far - (far - near) * depth_buffer)
print(f"\n[1단계: Z-buffer → Depth]")
print(f"depth_m = {depth_m:.4f}m = {depth_m*100:.2f}cm")

# 2. NDC 계산
ndc_x = (2.0 * pixel_x / WIDTH) - 1.0
ndc_y = 1.0 - (2.0 * pixel_y / HEIGHT)
ndc_z = 2.0 * depth_buffer - 1.0

print(f"\n[2단계: Pixel → NDC]")
print(f"NDC = ({ndc_x:.4f}, {ndc_y:.4f}, {ndc_z:.4f})")

# 3. Clip space
clip_coords = np.array([ndc_x, ndc_y, ndc_z, 1.0])
print(f"\n[3단계: Clip space]")
print(f"Clip = {clip_coords}")

# 4. 역변환
inv_proj = np.linalg.inv(proj_matrix)
inv_view = np.linalg.inv(view_matrix)

print(f"\n[4단계: Inverse matrices]")
print(f"inv_proj:\n{inv_proj}")
print(f"\ninv_view:\n{inv_view}")

# 5. View space
view_coords = inv_proj @ clip_coords
print(f"\n[5단계: Clip → View]")
print(f"View (before division) = {view_coords}")

if view_coords[3] != 0:
    view_coords = view_coords / view_coords[3]
print(f"View (after division) = {view_coords}")

# 6. World space
world_coords = inv_view @ view_coords
print(f"\n[6단계: View → World]")
print(f"World (m) = {world_coords}")
print(f"World (cm) = ({world_coords[0]*100:.2f}, {world_coords[1]*100:.2f}, {world_coords[2]*100:.2f})")

# 7. 예상값과 비교
print(f"\n[비교]")
print(f"예상 (PyBullet 물체): (10, 10, 2.5)cm")
print(f"계산 결과: ({world_coords[0]*100:.2f}, {world_coords[1]*100:.2f}, {world_coords[2]*100:.2f})cm")

print("\n" + "=" * 80)
