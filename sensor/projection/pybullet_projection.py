"""
PyBullet 픽셀→3D 좌표 변환

카메라 FOV와 view matrix를 모두 고려한 정확한 변환
"""

import numpy as np
import math
import logging

# PyBullet 카메라 설정
CAMERA_CONFIG = {
    "width": 600,
    "height": 480,
    "fov": 60,  # degrees
    "camera_pos": np.array([0.5, 0.0, 0.5]),  # m
    "target_pos": np.array([0.0, 0.0, 0.0]),
    "up_vector": np.array([0.0, 0.0, 1.0])
}


def get_camera_axes():
    """카메라 좌표계 축을 계산합니다."""
    cam_pos = CAMERA_CONFIG["camera_pos"]
    target = CAMERA_CONFIG["target_pos"]
    up = CAMERA_CONFIG["up_vector"]
    
    # Forward (카메라가 바라보는 방향)
    forward = target - cam_pos
    forward = forward / np.linalg.norm(forward)
    
    # Right (카메라의 오른쪽)
    right = np.cross(forward, up)
    right = right / np.linalg.norm(right)
    
    # Up (카메라의 위쪽, 재계산)
    up_actual = np.cross(right, forward)
    
    return right, up_actual, forward


# 전역 캐시
_camera_axes = None


def pixel_to_3d(pixel_x: int, pixel_y: int, depth_m: float) -> tuple:
    """
    PyBullet 픽셀 좌표를 로봇 베이스 3D 좌표(cm)로 변환합니다.
    
    FOV를 고려하여 정확한 각도로 ray를 쏩니다.
    
    Args:
        pixel_x: 픽셀 X 좌표
        pixel_y: 픽셀 Y 좌표  
        depth_m: 실제 깊이 (미터, 카메라 시선 방향)
    
    Returns:
        (x, y, z): 월드/로봇 베이스 좌표 cm 단위
    """
    global _camera_axes
    
    if _camera_axes is None:
        _camera_axes = get_camera_axes()
        logging.info("[PyBulletProjection] 카메라 좌표축 계산 완료")
    
    right, up, forward = _camera_axes
    
    width = CAMERA_CONFIG["width"]
    height = CAMERA_CONFIG["height"]
    fov = CAMERA_CONFIG["fov"]
    cam_pos = CAMERA_CONFIG["camera_pos"]
    
    # 1. FOV를 고려한 focal length 계산
    fov_rad = math.radians(fov)
    focal_length = (height / 2.0) / math.tan(fov_rad / 2.0)
    
    # 2. 픽셀을 카메라 중심에서의 오프셋으로 변환
    dx = pixel_x - width / 2.0
    dy = pixel_y - height / 2.0
    
    # 3. Ray direction 계산 (정규화된 방향)
    # ray = forward + (dx/focal_length) * right + (dy/focal_length) * up
    ray_dir = forward + (dx / focal_length) * right + (dy / focal_length) * up
    ray_dir = ray_dir / np.linalg.norm(ray_dir)
    
    # 4. Ray를 따라 depth만큼 이동
    # depth는 forward 방향이 아니라 ray 방향!
    world_pos = cam_pos + depth_m * ray_dir
    
    # 5. m → cm
    world_cm = world_pos * 100
    
    logging.info(f"[PyBulletProjection] "
                f"픽셀=({pixel_x}, {pixel_y}), depth={depth_m:.4f}m → "
                f"ray_dir=({ray_dir[0]:.3f}, {ray_dir[1]:.3f}, {ray_dir[2]:.3f}) → "
                f"월드좌표=({world_cm[0]:.2f}, {world_cm[1]:.2f}, {world_cm[2]:.2f})cm")
    
    return world_cm[0], world_cm[1], world_cm[2]
