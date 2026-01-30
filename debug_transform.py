#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
좌표 변환 디버깅: 각 단계별 값 확인
"""

import math
import numpy as np

print("=" * 80)
print("좌표 변환 디버깅")
print("=" * 80)

# 실제 값 (로그에서)
print("\n[로그 값]")
pixel_u, pixel_v = 367, 276
depth_m = 0.5940
print(f"픽셀: ({pixel_u}, {pixel_v})")
print(f"Depth: {depth_m}m")

# V2.0 현재 계산 (비례)
print("\n[V2.0 비례 계산]")
WIDTH, HEIGHT = 600, 480
z_cm = depth_m * 100.0
x_cm = (pixel_u - WIDTH/2) * (z_cm / WIDTH)
y_cm = (pixel_v - HEIGHT/2) * (z_cm / HEIGHT)
print(f"카메라 좌표: ({x_cm:.2f}, {y_cm:.2f}, {z_cm:.2f})cm")
print(f"오프셋 적용: ({x_cm+50:.2f}, {y_cm+0:.2f}, {z_cm+50:.2f})cm")

# PyBullet 실제 물체 위치
print("\n[PyBullet 실제]")
obj_pos = np.array([0.1, 0.1, 0.025])  # m
print(f"물체 위치: ({obj_pos[0]*100:.1f}, {obj_pos[1]*100:.1f}, {obj_pos[2]*100:.1f})cm")

# 카메라 위치 및 방향
print("\n[카메라 설정]")
cam_pos = np.array([0.5, 0.0, 0.5])  # m
cam_target = np.array([0.0, 0.0, 0.0])
print(f"카메라 위치: ({cam_pos[0]*100:.1f}, {cam_pos[1]*100:.1f}, {cam_pos[2]*100:.1f})cm")
print(f"카메라 타겟: (0, 0, 0)cm")

# 물체의 카메라 기준 상대 위치
print("\n[상대 위치 계산]")
rel_pos = obj_pos - cam_pos
print(f"상대 벡터: ({rel_pos[0]*100:.1f}, {rel_pos[1]*100:.1f}, {rel_pos[2]*100:.1f})cm")

# 카메라 시선 방향 (정규화)
view_dir = cam_target - cam_pos
view_dir = view_dir / np.linalg.norm(view_dir)
print(f"시선 방향 (정규화): ({view_dir[0]:.3f}, {view_dir[1]:.3f}, {view_dir[2]:.3f})")

# 카메라 좌표계로 변환 (회전 행렬 필요)
# 전방(forward) = view_dir
# 우측(right) = cross(view_dir, [0,0,1])
# 상단(up) = cross(right, forward)
up_world = np.array([0, 0, 1])
right = np.cross(view_dir, up_world)
right = right / np.linalg.norm(right)
up = np.cross(right, view_dir)

print(f"\n[카메라 좌표계 축]")
print(f"Right: ({right[0]:.3f}, {right[1]:.3f}, {right[2]:.3f})")
print(f"Up:    ({up[0]:.3f}, {up[1]:.3f}, {up[2]:.3f})")
print(f"Forward: ({view_dir[0]:.3f}, {view_dir[1]:.3f}, {view_dir[2]:.3f})")

# 카메라 좌표계로 변환
cam_x = np.dot(rel_pos, right) * 100  # cm
cam_y = np.dot(rel_pos, up) * 100
cam_z = -np.dot(rel_pos, view_dir) * 100  # depth (forward의 반대)

print(f"\n[올바른 카메라 좌표]")
print(f"({cam_x:.2f}, {cam_y:.2f}, {cam_z:.2f})cm")

print(f"\n[로봇 베이스 좌표 (오프셋 적용)]")
robot_x = cam_x + 50.0
robot_y = cam_y + 0.0
robot_z = cam_z + 50.0
print(f"({robot_x:.2f}, {robot_y:.2f}, {robot_z:.2f})cm")

print(f"\n[비교]")
print(f"PyBullet 실제:  (10.0, 10.0, 2.5)cm")
print(f"V2.0 현재 계산:  (56.63, 4.46, 109.40)cm ❌")
print(f"올바른 변환:     ({robot_x:.2f}, {robot_y:.2f}, {robot_z:.2f})cm")

print("\n" + "=" * 80)
