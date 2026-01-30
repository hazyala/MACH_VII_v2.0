#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
좌표 변환 단위 테스트

PyBullet 서버의 실제 물체 위치: (0.1, 0.1, 0.105)m = (10, 10, 10.5)cm
예상 픽셀: 중앙 근처
예상 depth: 약 0.7m (카메라 거리)
"""

import sys
import os

# UTF-8 출력 설정 (Windows 인코딩 문제 해결)
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sensor.projection import pybullet_projection
import numpy as np

print("=" * 80)
print("PyBullet 좌표 변환 검증 테스트")
print("=" * 80)

# 실제 PyBullet 물체 위치 (사용자 제공)
actual_obj_pos = np.array([0.1, 0.1, 0.105])  # m
print(f"\n[실제 물체 위치]")
print(f"  월드 좌표: ({actual_obj_pos[0]:.3f}, {actual_obj_pos[1]:.3f}, {actual_obj_pos[2]:.3f})m")
print(f"  월드 좌표: ({actual_obj_pos[0]*100:.1f}, {actual_obj_pos[1]*100:.1f}, {actual_obj_pos[2]*100:.1f})cm")

# 카메라 위치
cam_eye = np.array([0.5, 0.0, 0.5])
cam_target = np.array([0.0, 0.0, 0.0])

print(f"\n[카메라 설정]")
print(f"  카메라 위치: ({cam_eye[0]}, {cam_eye[1]}, {cam_eye[2]})m")
print(f"  카메라 타겟: ({cam_target[0]}, {cam_target[1]}, {cam_target[2]})m")

# 상대 벡터 및 거리 계산
rel_vec = actual_obj_pos - cam_eye
distance = np.linalg.norm(rel_vec)

print(f"\n[카메라→물체 벡터]")
print(f"  상대 벡터: ({rel_vec[0]:.3f}, {rel_vec[1]:.3f}, {rel_vec[2]:.3f})m")
print(f"  직선 거리: {distance:.4f}m")

# 테스트 케이스: 로그에서 얻은 실제 값 사용
print("\n" + "=" * 80)
print("테스트 케이스 1: 물체 중심부 (로그 기반 예상값)")
print("=" * 80)

# 예상 픽셀 좌표 (화면 중앙 근처)
# 물체가 (0.1, 0.1, 0.105)에 있고 카메라가 (0.5, 0, 0.5)에서 (0, 0, 0)을 바라봄
# 픽셀은 350 근처일 것으로 예상
test_pixel_x = 367  # 로그 기반
test_pixel_y = 276  # 로그 기반
test_depth_m = 0.5940  # 로그 기반

print(f"\n[입력값]")
print(f"  픽셀: ({test_pixel_x}, {test_pixel_y})")
print(f"  깊이: {test_depth_m:.4f}m")

# 좌표 변환 실행
result_x, result_y, result_z = pybullet_projection.pixel_to_3d(
    test_pixel_x, test_pixel_y, test_depth_m
)

print(f"\n[변환 결과]")
print(f"  계산된 월드 좌표: ({result_x:.2f}, {result_y:.2f}, {result_z:.2f})cm")
print(f"  실제 물체 위치:   ({actual_obj_pos[0]*100:.1f}, {actual_obj_pos[1]*100:.1f}, {actual_obj_pos[2]*100:.1f})cm")

# 오차 계산
error_x = abs(result_x - actual_obj_pos[0]*100)
error_y = abs(result_y - actual_obj_pos[1]*100)
error_z = abs(result_z - actual_obj_pos[2]*100)
total_error = np.sqrt(error_x**2 + error_y**2 + error_z**2)

print(f"\n[오차 분석]")
print(f"  X 오차: {error_x:.2f}cm")
print(f"  Y 오차: {error_y:.2f}cm")
print(f"  Z 오차: {error_z:.2f}cm")
print(f"  총 오차: {total_error:.2f}cm")

# 검증 기준: ±5cm 이내
print(f"\n[검증 결과]")
if total_error < 5.0:
    print(f"  ✅ 성공! (총 오차 {total_error:.2f}cm < 5cm)")
else:
    print(f"  ❌ 실패. (총 오차 {total_error:.2f}cm >= 5cm)")
    print(f"  디버깅 필요: 좌표 변환 로직 재검토")

print("\n" + "=" * 80)
