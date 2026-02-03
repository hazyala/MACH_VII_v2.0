import logging
import threading
import time
import numpy as np
from shared.config import GlobalConfig, CameraConfig
from ..implementations import PybulletVision, RealSenseVision
from .yolo_detector import YoloDetector
from state.system_state import system_state

class VisionBridge:
    """
    [Layer 1: Perception Bridge] 하드웨어 드라이버와 AI 모델을 연결하는 핵심 중계 계층입니다.
    
    이 클래스는 영상 소스(Real/Sim)를 관리하고, YOLO가 찾은 2D 픽셀 좌표를 
    로봇이 실제 팔을 뻗을 수 있는 3D cm 좌표로 변환하는 '좌표 정제' 프로세스를 총괄합니다.
    """
    def __init__(self):
        """
        초기 설정에 따라 비전 소스를 선택하고 탐지용 엔진을 준비합니다.
        """
        self.sim_mode = GlobalConfig.SIM_MODE
        self.yolo = YoloDetector()

        # 현재 모드에 맞는 소스 활성화
        if self.sim_mode:
            self._setup_virtual_source()
        else:
            self._setup_real_source()

    def _setup_virtual_source(self):
        """시뮬레이션(PyBullet) 비전 소스를 구성합니다."""
        self.driver = PybulletVision()
        self.offset = CameraConfig.SIM_OFFSET
        self.sim_mode = True
        logging.info("[VisionBridge] 가상 비전(Simulation) 소스 연결됨.")

    def _setup_real_source(self):
        """실물(RealSense) 비전 소스를 구성합니다."""
        self.driver = RealSenseVision()
        self.offset = CameraConfig.REAL_OFFSET
        self.sim_mode = False
        logging.info("[VisionBridge] 실물 비전(RealSense) 소스 연결됨.")

    def switch_source(self, source: str):
        """
        실시간으로 카메라 소스를 전환합니다. (UI 요청 등에 대응)
        
        Args:
            source: 'virtual' 또는 'real'
        """
        from shared.ui_dto import CameraSource
        if source == CameraSource.VIRTUAL:
            self._setup_virtual_source()
        else:
            self._setup_real_source()
        logging.info(f"[VisionBridge] 비전 소스가 {source}로 전환되었습니다.")

    def get_raw_frame(self):
        """
        VLM 분석 등을 위해 보정되지 않은 순수 원본 영상 프레임을 반환합니다.
        """
        packet = self.driver.get_synced_packet()
        return packet.get("color") if packet else None

    def get_refined_detections(self) -> list:
        """
        [Core Logic] 픽셀 좌표를 로봇 기준 3D cm 좌표로 정밀 변환합니다.
        
        흐름: 
        1. 동기화된 데이터(Color/Depth/Pose) 획득
        2. YOLO 2D 탐지 실행
        3. ROI 분석 및 적응형 깊이 추정 (Spherical Compensation)
        4. 카메라 오프셋 보정 및 로봇 베이스 좌표 산출
        """
        # 1. 동기화 패킷 획득
        packet = self.driver.get_synced_packet()
        if not packet:
            return []

        color_frame = packet.get("color")
        depth_frame = packet.get("depth")
        captured_pose = packet.get("captured_pose", {})
        
        if color_frame is None or depth_frame is None:
            return []

        # 2. YOLO 2D 객체 탐지
        raw_detections = self.yolo.detect(color_frame)
        
        refined_list = []
        for det in raw_detections:
            u, v = det["pixel_center"]
            
            # 3. [ROI(Region of Interest: 이미지 내에서 분석하고자 하는 특정 관심 영역) 기반 고정밀 깊이 추출]
            # 단순히 한 점(u, v)의 깊이만 읽으면 노이즈에 취약합니다.
            # 물체 중심부의 영역(ROI)을 통계적으로 분석하여 대표 깊이를 산출합니다.
            
            # BBox(경계 상자)의 중앙 40% 영역만 추출 (배경 노이즈 배제)
            margin_w = int(det["bbox"][0] * 0.3)
            margin_h = int(det["bbox"][1] * 0.3)
            
            u_min = max(0, u - det["bbox"][0] // 2 + margin_w)
            u_max = min(depth_frame.shape[1], u + det["bbox"][0] // 2 - margin_w)
            v_min = max(0, v - det["bbox"][1] // 2 + margin_h)
            v_max = min(depth_frame.shape[0], v + det["bbox"][1] // 2 - margin_h)
            
            depth_roi = depth_frame[v_min:v_max, u_min:u_max]
            
            # 유효 범위(0.1m ~ 3.0m) 필터링
            valid_depths = depth_roi[(depth_roi > 0.1) & (depth_roi < 3.0)]
            
            if len(valid_depths) > 0:
                # [적응형 중심 추정 - Spherical Compensation(구면 보정: 렌즈 굴곡으로 인한 거리 오차를 바로잡는 것)]
                # 물체는 표면(Surface)만 찍히지만, 로봇은 중심(Center)을 잡아야 합니다.
                # 알고리즘: Median(중간값: 데이터의 한가운데 값) + Std(표준편차: 데이터가 퍼진 정도, 여기서는 물체의 곡률 반영)
                # 입체적인 물체일수록 Std가 크므로 더 깊은 곳(중심)을 바라보게 됩니다.
                median_d = float(np.median(valid_depths))
                std_d = float(np.std(valid_depths))
                depth_m = median_d + std_d
            else:
                # ROI 분석 불가 시 중앙점 값 사용 (Fallback: 대비책)
                depth_m = depth_frame[v, u] if v < depth_frame.shape[0] and u < depth_frame.shape[1] else 0
            
            if depth_m <= 0.1: continue

            # 4. 픽셀-to-3D 변환 (cm 단위)
            coords_cm = self.driver.pixel_to_cm(u, v, depth_m)
            
            if coords_cm:
                # 5. [좌표계 통합] 카메라 좌표 -> 로봇 베이스 좌표
                # 시뮬레이션은 이미 월드 좌표이므로 오프셋 불필요
                if type(self.driver).__name__ == "PybulletVision":
                    rx, ry, rz = coords_cm
                    log_type = "월드(GT보정: 실제 정답값 기준)"
                else:
                    # 실물은 카메라 위치 오프셋(설치 위치 차이)을 더함
                    rx = coords_cm[0] + self.offset["x"]
                    ry = coords_cm[1] + self.offset["y"]
                    rz = coords_cm[2] + self.offset["z"]
                    log_type = "로봇베이스"
                
                logging.info(f"[VisionBridge] 탐지 완료: '{det['name']}' -> {log_type}=({rx:.2f}, {ry:.2f}, {rz:.2f})cm")

                refined_list.append({
                    "name": det["name"],
                    "position": {"x": round(rx, 2), "y": round(ry, 2), "z": round(rz, 2)},
                    "bbox": det["bbox"],
                    "sync_pose": captured_pose
                })
                
        return refined_list

    # NOTE: 백그라운드 업데이트 루프는 PerceptionManager에서 통합 관리하므로
    # 이 클래스 내부의 중복된 루프 로직은 제거되었습니다.

