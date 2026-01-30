"""
PyBullet 픽셀→3D 좌표 변환

Planar Depth(Z-depth) 기반 정확한 Pinhole 카메라 역투영 공식을 사용합니다.
프로젝트 좌표계: X(앞+), Y(왼쪽+), Z(위+)
"""

import logging
import numpy as np
import math

# PyBullet 카메라 설정 (pybullet_sim.py와 일치)
CAMERA_CONFIG = {
    "width": 600,
    "height": 480,
    "fov": 60,  # degrees (수직 FOV)
    "near": 0.01,
    "far": 10.0,
    "camera_eye": np.array([0.5, 0.0, 0.5]),     # 카메라 위치 (m)
    "camera_target": np.array([0.0, 0.0, 0.0]),  # 카메라 타겟 (m)
    "camera_up": np.array([0.0, 0.0, 1.0])       # 상단 벡터
}


def _calculate_intrinsics():
    """
    FOV로부터 카메라 Intrinsic 파라미터 계산
    
    Returns:
        (fx, fy, cx, cy): 초점 거리 및 주점 좌표 (pixels)
    """
    width = CAMERA_CONFIG["width"]
    height = CAMERA_CONFIG["height"]
    fov_deg = CAMERA_CONFIG["fov"]
    
    # 수직 FOV → 초점 거리
    # fy = height / (2 * tan(fov_y / 2))
    fov_rad = math.radians(fov_deg)
    fy = height / (2.0 * math.tan(fov_rad / 2.0))
    
    # 가로세로 비율 고려
    aspect = width / height
    fx = fy * aspect
    
    # 주점 (이미지 중심)
    cx = width / 2.0
    cy = height / 2.0
    
    return fx, fy, cx, cy


# Intrinsic 파라미터 미리 계산
FX, FY, CX, CY = _calculate_intrinsics()

logging.info(f"[PyBulletProjection] Intrinsic 파라미터: fx={FX:.2f}, fy={FY:.2f}, cx={CX:.2f}, cy={CY:.2f}")


def pixel_to_3d(pixel_x: int, pixel_y: int, depth_m: float) -> tuple:
    """
    PyBullet 픽셀 좌표를 월드 3D 좌표(cm)로 변환합니다.
    
    Depth는 Planar Depth(카메라 평면으로부터의 수직 거리, Z-depth)입니다.
    
    변환 과정:
    1. 픽셀 → 카메라 로컬 좌표 (Pinhole 역투영)
    2. 카메라 로컬 → 월드 좌표 (View Matrix 역변환)
    
    Args:
        pixel_x: 픽셀 u 좌표 (0 ~ width-1)
        pixel_y: 픽셀 v 좌표 (0 ~ height-1)
        depth_m: Planar Depth (m, 카메라 Z축 방향 거리)
    
    Returns:
        (x, y, z): 월드 좌표 cm 단위 (X:앞+, Y:왼쪽+, Z:위+)
    """
    
    # === 1단계: 픽셀 → 카메라 로컬 좌표 (Pinhole 역투영) ===
    # 
    # 핵심 공식 (Planar Depth 기반):
    # x_cam = (u - cx) * (depth / fx)
    # y_cam = (cy - v) * (depth / fy)  ← Y축 반전!
    # z_cam = depth
    #
    # 이미지 좌표계: 좌상단(0,0), 오른쪽(+u), 아래(+v)
    # 카메라 좌표계: Right(+X_cam), Up(+Y_cam), Forward(+Z_cam)
    
    X_cam = (pixel_x - CX) * (depth_m / FX)
    Y_cam = (CY - pixel_y) * (depth_m / FY)  # Y축 반전: cy - v
    Z_cam = depth_m
    
    # === 2단계: 카메라 좌표계 기저 벡터 계산 ===
    cam_eye = CAMERA_CONFIG["camera_eye"]
    cam_target = CAMERA_CONFIG["camera_target"]
    cam_up = CAMERA_CONFIG["camera_up"]
    
    # Forward (카메라 시선 방향, 정규화)
    forward = cam_target - cam_eye
    forward = forward / np.linalg.norm(forward)
    
    # Right (카메라 오른쪽 방향)
    right = np.cross(forward, cam_up)
    right = right / np.linalg.norm(right)
    
    # Up (카메라 위쪽 방향, 직교성 보장)
    up = np.cross(right, forward)
    
    # === 3단계: 카메라 로컬 → 월드 좌표 변환 ===
    #
    # 카메라 좌표계 → 월드 좌표계 변환:
    # - X_cam: Right 방향
    # - Y_cam: Up 방향
    # - Z_cam: Forward 방향
    #
    # world_pos = camera_eye + Right * X_cam + Up * Y_cam + Forward * Z_cam
    
    cam_local = np.array([X_cam, Y_cam, Z_cam])
    world_pos_m = (
        cam_eye + 
        right * cam_local[0] + 
        up * cam_local[1] + 
        forward * cam_local[2]
    )
    
    # === 4단계: m → cm 변환 ===
    x_cm = world_pos_m[0] * 100.0
    y_cm = world_pos_m[1] * 100.0
    z_cm = world_pos_m[2] * 100.0
    
    logging.info(
        f"[PyBulletProjection] "
        f"픽셀=({pixel_x}, {pixel_y}), depth={depth_m:.4f}m → "
        f"카메라로컬=({X_cam:.4f}, {Y_cam:.4f}, {Z_cam:.4f})m → "
        f"월드좌표=({x_cm:.2f}, {y_cm:.2f}, {z_cm:.2f})cm"
    )
    
    return x_cm, y_cm, z_cm
