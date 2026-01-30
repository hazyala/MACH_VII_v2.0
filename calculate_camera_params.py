#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PyBullet 카메라 intrinsic 파라미터 계산

PyBullet의 FOV 기반 카메라에서 정확한 fx, fy, cx, cy 계산
"""

import numpy as np
import math

# PyBullet 카메라 설정 (pybullet_sim.py 참조)
WIDTH = 600
HEIGHT = 480
FOV = 60  # degrees
ASPECT = WIDTH / HEIGHT
NEAR = 0.01
FAR = 10.0

print("=" * 70)
print("PyBullet 카메라 Intrinsic 파라미터 계산")
print("=" * 70)

print(f"\n[입력 파라미터]")
print(f"  해상도: {WIDTH} x {HEIGHT}")
print(f"  FOV (수직): {FOV}°")
print(f"  Aspect Ratio: {ASPECT:.3f}")
print(f"  Near/Far: {NEAR}m / {FAR}m")

# FOV를 focal length로 변환
# fy = height / (2 * tan(fov_y / 2))
fov_y_rad = math.radians(FOV)
fy = HEIGHT / (2.0 * math.tan(fov_y_rad / 2.0))

# fx는 aspect ratio를 고려
fx = fy * ASPECT

# 주점 (이미지 중심)
cx = WIDTH / 2.0
cy = HEIGHT / 2.0

print(f"\n[계산된 Intrinsic 파라미터]")
print(f"  fx = {fx:.2f} pixels")
print(f"  fy = {fy:.2f} pixels")
print(f"  cx = {cx:.2f} pixels")
print(f"  cy = {cy:.2f} pixels")

# 검증: 픽셀 (367, 276), depth 0.594m를 3D로 변환
print(f"\n[검증: 표준 Pinhole 카메라 모델]")
pixel_x = 367
pixel_y = 276
depth_m = 0.594

# Normalized Image Coordinates
x_norm = (pixel_x - cx) / fx
y_norm = (pixel_y - cy) / fy

# 3D Camera Coordinates
X_cam = x_norm * depth_m
Y_cam = y_norm * depth_m
Z_cam = depth_m

print(f"  픽셀: ({pixel_x}, {pixel_y})")
print(f"  깊이: {depth_m:.4f}m")
print(f"  정규화 좌표: ({x_norm:.4f}, {y_norm:.4f})")
print(f"  카메라 좌표: ({X_cam:.4f}, {Y_cam:.4f}, {Z_cam:.4f})m")
print(f"  카메라 좌표: ({X_cam*100:.2f}, {Y_cam*100:.2f}, {Z_cam*100:.2f})cm")

# 카메라 → 월드 좌표 변환
print(f"\n[카메라 → 월드 좌표 변환]")
cam_eye = np.array([0.5, 0.0, 0.5])  # m
cam_target = np.array([0.0, 0.0, 0.0])
cam_up = np.array([0.0, 0.0, 1.0])

# Forward (카메라 → 타겟)
forward = cam_target - cam_eye
forward = forward / np.linalg.norm(forward)

# Right
right = np.cross(forward, cam_up)
right = right / np.linalg.norm(right)

# Up (재계산)
up = np.cross(right, forward)

print(f"  카메라 위치: {cam_eye}")
print(f"  Forward: {forward}")
print(f"  Right: {right}")
print(f"  Up: {up}")

# 월드 좌표 = 카메라 위치 + 회전 변환
# 주의: PyBullet 카메라는 -Z를 바라보므로 Z 부호 조정 필요
cam_local = np.array([X_cam, Y_cam, Z_cam])

# 회전 행렬 적용 (카메라 좌표 → 월드 좌표)
world_pos = cam_eye + right * cam_local[0] + up * cam_local[1] + forward * cam_local[2]

print(f"\n[월드 좌표 계산 결과]")
print(f"  월드 좌표: ({world_pos[0]:.4f}, {world_pos[1]:.4f}, {world_pos[2]:.4f})m")
print(f"  월드 좌표: ({world_pos[0]*100:.2f}, {world_pos[1]*100:.2f}, {world_pos[2]*100:.2f})cm")

print(f"\n[비교]")
print(f"  실제 물체 위치: (10.0, 10.0, 10.5)cm")
print(f"  계산된 위치:    ({world_pos[0]*100:.2f}, {world_pos[1]*100:.2f}, {world_pos[2]*100:.2f})cm")

error = np.array([10.0, 10.0, 10.5]) - world_pos * 100
total_error = np.linalg.norm(error)
print(f"  오차: ({error[0]:.2f}, {error[1]:.2f}, {error[2]:.2f})cm")
print(f"  총 오차: {total_error:.2f}cm")

print("\n" + "=" * 70)
