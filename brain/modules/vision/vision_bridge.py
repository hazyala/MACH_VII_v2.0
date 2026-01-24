# brain/modules/vision/vision_bridge.py

import streamlit as st
# core 및 modules 레이어에서 필요한 기능을 임포트합니다.
from core.vision_base import VisionBase
# 추후 구현될 실제 드라이버들입니다.
# from core.pybullet_vision import PyBulletVision
# from core.realsense_vision import RealSenseVision
from brain.modules.vision.yolo_detector import YoloDetector

class VisionBridge:
    """
    비전 드라이버와 분석 알고리즘을 연결하는 중계 클래스입니다.
    데이터 획득, 객체 인식, 3D 좌표 변환 과정을 통합 관리합니다.
    """
    def __init__(self):
        self.sim_mode = st.session_state.get("sim_mode", True)
        # 현재 환경에 적합한 비전 드라이버를 초기화합니다.
        self.driver = self._init_driver()
        # YOLOv11 엔진을 초기화합니다.
        self.yolo = YoloDetector()

    def _init_driver(self) -> VisionBase:
        """시스템 모드에 따라 가상 또는 실물 카메라 드라이버를 반환합니다."""
        if self.sim_mode:
            # return PyBulletVision()
            return None
        else:
            # return RealSenseVision()
            return None

    def get_refined_detections(self):
        """
        영상 획득부터 좌표 정제까지의 전 과정을 수행하여 최종 결과를 반환합니다.
        """
        if not self.driver:
            return []

        # 1. 카메라로부터 RGB 영상과 Depth 데이터를 동기화하여 가져옵니다.
        # frame_data 형식: {"color": numpy_array, "depth": numpy_array}
        frame_data = self.driver.get_frame()
        if frame_data is None:
            return []

        # 2. YOLO 엔진을 사용하여 2D 픽셀 좌표와 객체 명칭을 추출합니다.
        raw_detections = self.yolo.detect(frame_data["color"])
        
        refined_results = []
        for det in raw_detections:
            # 3. 픽셀 좌표와 Depth 값을 이용하여 3D cm 좌표로 변환합니다.
            # 이 과정에서 VisionBase 내부에 정의된 칼만 필터가 자동으로 적용됩니다.
            u, v = det["pixel_center"] # 객체 중심점 픽셀
            depth_val = frame_data["depth"][v, u] # 해당 지점의 깊이 값
            
            coords_cm = self.driver.pixel_to_cm(u, v, depth_val)
            
            if coords_cm:
                refined_results.append({
                    "name": det["name"],
                    "position": {
                        "x": coords_cm[0],
                        "y": coords_cm[1],
                        "z": coords_cm[2]
                    }
                })
                
        return refined_results