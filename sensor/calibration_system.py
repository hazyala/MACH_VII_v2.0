import cv2
import numpy as np
import json
import logging
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple, Dict

@dataclass
class CalibrationPoint:
    robot_x: float
    robot_y: float
    robot_z: float
    camera_x: float
    camera_y: float
    camera_z: float

class RedTapeDetector:
    """
    [Vision] 빨간색 테이프 마커를 검출하여 이미지 상의 중심점(u, v)을 반환합니다.
    HSV 색상 공간을 사용하여 빨간색 범위를 필터링합니다.
    """
    def __init__(self):
        # 빨간색은 HSV에서 0~10, 170~180 두 구간에 걸쳐 있음
        # Lower Red range 1
        self.lower_red1 = np.array([0, 120, 70])
        self.upper_red1 = np.array([10, 255, 255])
        
        # Lower Red range 2
        self.lower_red2 = np.array([170, 120, 70])
        self.upper_red2 = np.array([180, 255, 255])
        
    def detect(self, color_frame: np.ndarray, depth_frame: np.ndarray = None) -> Optional[Tuple[int, int, float]]:
        """
        이미지에서 가장 큰 빨간색 영역의 중심점(u, v)과 해당 지점의 depth(m)를 반환합니다.
        
        Returns:
            (u, v, depth_m) 튜플. 검출 실패 시 None 반환.
        """
        if color_frame is None:
            return None
            
        hsv = cv2.cvtColor(color_frame, cv2.COLOR_BGR2HSV)
        
        # 두 범위의 마스크 생성 및 합치기
        mask1 = cv2.inRange(hsv, self.lower_red1, self.upper_red1)
        mask2 = cv2.inRange(hsv, self.lower_red2, self.upper_red2)
        mask = mask1 + mask2
        
        # 노이즈 제거 (Opening)
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # 윤곽선 검출
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
            
        # 가장 큰 윤곽선 선택
        largest_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest_contour)
        
        # 너무 작은 영역은 무시
        if area < 100:
            return None
            
        # 중심점 계산 (모멘트)
        M = cv2.moments(largest_contour)
        if M["m00"] == 0:
            return None
            
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
        
        # Depth 값 추출 (만약 depth_frame이 제공되었다면)
        depth_val = 0.0
        if depth_frame is not None:
            # 주변 픽셀 평균으로 안정화
            depth_val = self._get_average_depth(depth_frame, cX, cY)
            
        return cX, cY, depth_val
    
    def _get_average_depth(self, depth_frame, u, v, kernel_size=3):
        """주변 픽셀의 깊이 평균을 구합니다 (0인 값 제외)"""
        h, w = depth_frame.shape
        half = kernel_size // 2
        
        valid_depths = []
        for y in range(max(0, v - half), min(h, v + half + 1)):
            for x in range(max(0, u - half), min(w, u + half + 1)):
                d = depth_frame[y, x]
                if d > 0:
                    valid_depths.append(d)
        
        if not valid_depths:
            return 0.0
            
        # 미터 단위 변환 (RealSense depth scale이 보통 0.001m = 1mm)
        # depth_frame이 이미 미터 단위인지 확인 필요. 보통 uint16(mm)임.
        return (sum(valid_depths) / len(valid_depths)) * 0.001

class CameraCalibrator:
    """
    [System] 카메라-로봇 간 좌표 변환 시스템
    Affine 변환 행렬을 사용하여 3D 카메라 좌표를 3D 로봇 좌표로 변환합니다.
    """
    def __init__(self, calibration_file: Path):
        self.calibration_file = calibration_file
        self.points: List[CalibrationPoint] = []
        self.transform_matrix = None # 4x4 행렬
        self.load_calibration()
        
    def add_point(self, robot_pos: Tuple[float, float, float], camera_pos: Tuple[float, float, float]):
        """캘리브레이션 포인트 추가"""
        point = CalibrationPoint(
            robot_x=robot_pos[0], robot_y=robot_pos[1], robot_z=robot_pos[2],
            camera_x=camera_pos[0], camera_y=camera_pos[1], camera_z=camera_pos[2]
        )
        self.points.append(point)
        logging.info(f"[Calibration] 포인트 추가됨: R{robot_pos} <-> C{camera_pos}")
        
    def clear_points(self):
        self.points = []
        
    def calculate_transform(self) -> bool:
        """
        수집된 포인트들을 사용하여 최적의 Affine 변환 행렬을 계산합니다.
        최소 4개의 포인트가 필요합니다 (RANSAC 권장).
        """
        if len(self.points) < 4:
            logging.error(f"[Calibration] 포인트 부족. 최소 4개 필요 (현재: {len(self.points)})")
            return False
            
        try:
            # 입력 (Camera) -> 출력 (Robot)
            src_pts = np.array([[p.camera_x, p.camera_y, p.camera_z] for p in self.points], dtype=np.float32)
            dst_pts = np.array([[p.robot_x, p.robot_y, p.robot_z] for p in self.points], dtype=np.float32)
            
            # Affine 3D 변환 행렬 계산 (OpenCV estimateAffine3D 사용)
            # retval: 성공 여부, matrix: 3x4 행렬, inliers
            retval, matrix, inliers = cv2.estimateAffine3D(src_pts, dst_pts)
            
            if not retval:
                logging.error("[Calibration] 변환 행렬 계산 실패")
                return False
                
            # 4x4 행렬로 확장
            self.transform_matrix = np.eye(4)
            self.transform_matrix[:3, :] = matrix
            
            logging.info("[Calibration] 변환 행렬 계산 성공")
            logging.info(f"\n{self.transform_matrix}")
            return True
            
        except Exception as e:
            logging.error(f"[Calibration] 계산 중 오류 발생: {e}")
            return False
            
    def save_calibration(self):
        """캘리브레이션 결과를 JSON 파일로 저장"""
        if self.transform_matrix is None:
            logging.warning("[Calibration] 저장할 변환 행렬이 없습니다.")
            return

        data = {
            "transform_matrix": self.transform_matrix.tolist(),
            "points": [asdict(p) for p in self.points],
            "timestamp": cv2.getTickCount()
        }
        
        try:
            self.calibration_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.calibration_file, 'w') as f:
                json.dump(data, f, indent=4)
            logging.info(f"[Calibration] 저장 완료: {self.calibration_file}")
        except Exception as e:
            logging.error(f"[Calibration] 저장 실패: {e}")

    def load_calibration(self):
        """캘리브레이션 파일 로드"""
        if not self.calibration_file.exists():
            logging.warning(f"[Calibration] 파일 없음: {self.calibration_file}")
            return
            
        try:
            with open(self.calibration_file, 'r') as f:
                data = json.load(f)
                
            matrix = np.array(data["transform_matrix"])
            if matrix.shape == (4, 4):
                self.transform_matrix = matrix
                logging.info(f"[Calibration] 로드 완료: {self.calibration_file}")
                # 포인트 데이터는 선택적으로 로드
                if "points" in data:
                    self.points = [CalibrationPoint(**p) for p in data["points"]]
            else:
                logging.error(f"[Calibration] 잘못된 행렬 형상: {matrix.shape}")
                
        except Exception as e:
            logging.error(f"[Calibration] 로드 실패: {e}")

    def camera_to_robot(self, x: float, y: float, z: float) -> Tuple[float, float, float]:
        """
        카메라 좌표(cm)를 로봇 좌표(cm)로 변환합니다.
        캘리브레이션이 안 되어 있으면 기본 오프셋만 적용하거나 원본 반환.
        """
        if self.transform_matrix is None:
            # Fallback: config.py의 단순 오프셋 사용 (기존 방식)
            # 여기서는 편의상 입력값 그대로 반환하거나 경고 출력
            # logging.warning("[Calibration] 변환 행렬 없음. 원본 좌표 반환")
            return x, y, z
            
        # Homogeneous 좌표로 변환 [x, y, z, 1]
        vec = np.array([x, y, z, 1.0])
        transformed = self.transform_matrix @ vec
        
        return float(transformed[0]), float(transformed[1]), float(transformed[2])
