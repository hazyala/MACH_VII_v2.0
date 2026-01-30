#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Forward Projection 검증: 월드 좌표 → 픽셀 계산

물체가 (10, 10, 10.5)cm = (0.1, 0.1, 0.105)m에 있을 때
예상되는 픽셀 위치와 depth를 계산합니다.
"""

import numpy as np
import math

# 카메라 설정
WIDTH, HEIGHT = 600, 480
FOV = 60  # degrees
cam_eye = np.array([0.5, 0.0, 0.5])  # m
cam_target = np.array([0.0, 0.0, 0.0])
cam_up = np.array([0.0, 0.0, 1.0])

# 물체 위치
obj_world = np.array([0.1, 0.1, 0.105])  # m

print("=" * 70)
print("Forward Projection: 월드 좌표 → 픽셀")
print("=" * 70)

# Intrinsic 계산
fov_rad = math.radians(FOV)
fy = HEIGHT / (2.0 * math.tan(fov_rad / 2.0))
fx = fy * (WIDTH / HEIGHT)
cx = WIDTH / 2.0
cy = HEIGHT / 2.0

print(f"\n[Intrinsic 파라미터]")
print(f"  fx = {fx:.2f}, fy = {fy:.2f}")
print(f"  cx = {cx:.2f}, cy = {cy:.2f}")

# 카메라 좌표계 기저 벡터
forward = cam_target - cam_eye
forward = forward / np.linalg.norm(forward)

right = np.cross(forward, cam_up)
right = right / np.linalg.norm(right)

up = np.cross(right, forward)

print(f"\n[카메라 좌표계]")
print(f"  Eye: {cam_eye}")
print(f"  Forward: {forward}")
print(f"  Right: {right}")
print(f"  Up: {up}")

# 월드 → 카메라 변환
rel_vec = obj_world - cam_eye
X_cam = np.dot(rel_vec, right)
Y_cam = np.dot(rel_vec, up)
Z_cam = np.dot(rel_vec, forward)

print(f"\n[월드 → 카메라 변환]")
print(f"  물체 월드: {obj_world} m")
print(f"  상대 벡터: {rel_vec} m")
print(f"  카메라 좌표: ({X_cam:.4f}, {Y_cam:.4f}, {Z_cam:.4f}) m")

# 카메라 → 픽셀 투영 (Planar Depth 기반)
# u = cx + (X_cam / Z_cam) * fx
# v = cy - (Y_cam / Z_cam) * fy  ← Y축 반전

if Z_cam > 0:
    u = cx + (X_cam / Z_cam) * fx
    v = cy - (Y_cam / Z_cam) * fy  # Y축 반전
    
    print(f"\n[카메라 → 픽셀 투영]")
    print(f"  예상 픽셀: ({u:.1f}, {v:.1f})")
    print(f"  Planar Depth: {Z_cam:.4f} m")
else:
    print("\n물체가 카메라 뒤에 있습니다!")
    u, v = -1, -1

print(f"\n[비교]")
print(f"  로그 픽셀: (367, 276)")
print(f"  예상 픽셀: ({u:.1f}, {v:.1f})")
print(f"  로그 depth: 0.594m")
print(f"  예상 depth: {Z_cam:.4f}m")

# 역투영 검증
print(f"\n[역투영 검증]")
if u > 0 and v > 0:
    X_cam_back = (u - cx) * (Z_cam / fx)
    Y_cam_back = (cy - v) * (Z_cam / fy)
    Z_cam_back = Z_cam
    
    world_back = cam_eye + right * X_cam_back + up * Y_cam_back + forward * Z_cam_back
    
    print(f"  역투영 월드: {world_back} m")
    print(f"  역투영 월드: ({world_back[0]*100:.2f}, {world_back[1]*100:.2f}, {world_back[2]*100:.2f}) cm")
    print(f"  원본 월드:   (10.0, 10.0, 10.5) cm")
    
    error = world_back - obj_world
    print(f"  오차: ({error[0]*100:.2f}, {error[1]*100:.2f}, {error[2]*100:.2f}) cm")

print("\n" + "=" * 70)
