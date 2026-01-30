#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
실측 기반 변환 파라미터 역산
"""

import numpy as np

print("=" * 80)
print("좌표 변환 파라미터 역산")
print("=" * 80)

# 알려진 값
print("\n[알려진 정보]")
pixel_x, pixel_y = 367, 276
depth_m = 0.5940
width, height = 600, 480

# 비례 계산으로 카메라 좌표 (V2.0에서 계산된 값)
z_m = depth_m
x_m = (pixel_x - width/2) * (z_m / width)
y_m = (pixel_y - height/2) * (z_m / height)

print(f"픽셀: ({pixel_x}, {pixel_y})")
print(f"Depth: {depth_m}m")
print(f"카메라 좌표 (계산): ({x_m*100:.2f}, {y_m*100:.2f}, {z_m*100:.2f})cm")

# 실제 물체 위치 (PyBullet 월드 좌표)
obj_world = np.array([0.1, 0.1, 0.025])  # m
print(f"실제 물체 위치 (PyBullet): ({obj_world[0]*100:.1f}, {obj_world[1]*100:.1f}, {obj_world[2]*100:.1f})cm")

# 로봇 베이스가 (0,0,0)이라고 가정
# 즉, PyBullet 월드 좌표 = 로봇 베이스 좌표
robot_target = obj_world * 100  # cm

print(f"목표 로봇 베이스 좌표: ({robot_target[0]:.1f}, {robot_target[1]:.1f}, {robot_target[2]:.1f})cm")

# 카메라 좌표에서 로봇 베이스 좌표로 가는 변환 찾기
# robot = A @ camera + offset

camera_coords = np.array([x_m, y_m, z_m]) * 100  # cm

print(f"\n[변환 역산]")
print(f"카메라 좌표: ({camera_coords[0]:.2f}, {camera_coords[1]:.2f}, {camera_coords[2]:.2f})cm")
print(f"→ 로봇 베이스: ({robot_target[0]:.2f}, {robot_target[1]:.2f}, {robot_target[2]:.2f})cm")

# 간단한 선형 변환 시도
# robot_x = a1*cam_x + a2*cam_y + a3*cam_z + offset_x
# robot_y = b1*cam_x + b2*cam_y + b3*cam_z + offset_y  
# robot_z = c1*cam_x + c2*cam_y + c3*cam_z + offset_z

# V1.0 축 변환:
# robot_x = cam_z + offset_x
# robot_y = -cam_x + offset_y
# robot_z = -cam_y + offset_z

# 오프셋 계산
offset_x = robot_target[0] - camera_coords[2]
offset_y = robot_target[1] + camera_coords[0]
offset_z = robot_target[2] + camera_coords[1]

print(f"\n[V1.0 축 변환 가정시 필요한 오프셋]")
print(f"offset_x = {robot_target[0]:.2f} - {camera_coords[2]:.2f} = {offset_x:.2f}cm")
print(f"offset_y = {robot_target[1]:.2f} - (-{camera_coords[0]:.2f}) = {offset_y:.2f}cm")
print(f"offset_z = {robot_target[2]:.2f} - (-{camera_coords[1]:.2f}) = {offset_z:.2f}cm")

# 검증
robot_calc_x = camera_coords[2] + offset_x
robot_calc_y = -camera_coords[0] + offset_y
robot_calc_z = -camera_coords[1] + offset_z

print(f"\n[검증]")
print(f"계산된 로봇 좌표: ({robot_calc_x:.2f}, {robot_calc_y:.2f}, {robot_calc_z:.2f})cm")
print(f"목표 로봇 좌표:   ({robot_target[0]:.2f}, {robot_target[1]:.2f}, {robot_target[2]:.2f})cm")

if np.allclose([robot_calc_x, robot_calc_y, robot_calc_z], robot_target, atol=0.1):
    print("✅ 일치!")
else:
    print("❌ 불일치 - 다른 변환 필요")
    
    # 단순 offset만으로 시도
    print(f"\n[단순 오프셋 시도]")
    offset_simple_x = robot_target[0] - camera_coords[0]
    offset_simple_y = robot_target[1] - camera_coords[1]
    offset_simple_z = robot_target[2] - camera_coords[2]
    
    print(f"offset = ({offset_simple_x:.2f}, {offset_simple_y:.2f}, {offset_simple_z:.2f})cm")
    
    robot_simple_x = camera_coords[0] + offset_simple_x
    robot_simple_y = camera_coords[1] + offset_simple_y
    robot_simple_z = camera_coords[2] + offset_simple_z
    
    print(f"결과: ({robot_simple_x:.2f}, {robot_simple_y:.2f}, {robot_simple_z:.2f})cm")

print("\n" + "=" * 80)
