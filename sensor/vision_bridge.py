# sensor/vision_bridge.py

import streamlit as st
from shared.config import GlobalConfig, CameraConfig
from sensor.pybullet_vision import PybulletVision
# from sensor.realsense_vision import RealSenseVision # 실물 드라이버 구현 시 주석 해제
from sensor.yolo_detector import YoloDetector

class VisionBridge:
    """
    하드웨어 드라이버와 AI 모델을 연결하고, 동기화된 데이터를 바탕으로
    로봇 베이스 기준의 정밀 좌표를 산출하는 통합 관리 클래스입니다.
    """
    def __init__(self):
        # 1. 시스템 설정에서 시뮬레이션 모드 여부를 확인합니다.
        self.sim_mode = st.session_state.get("sim_mode", GlobalConfig.SIM_MODE)

        # 2. 모드에 따라 적절한 드라이버와 카메라 오프셋을 설정합니다.
        if self.sim_mode:
            self.driver = PybulletVision()
            self.offset = CameraConfig.SIM_OFFSET
        else:
            # self.driver = RealSenseVision()
            self.offset = CameraConfig.REAL_OFFSET

        # 3. 객체 탐지를 위한 YOLOv11 엔진을 초기화합니다.
        self.yolo = YoloDetector()

    def get_raw_frame(self):
        """
        VLM 분석을 위해 처리되지 않은 원본 영상 데이터를 반환합니다.
        동기화 패키지에서 컬러 영상만 추출하여 제공합니다.
        """
        packet = self.driver.get_synced_packet()
        if not packet:
            return None
        return packet.get("color")

    def get_refined_detections(self):
        """
        동기화된 영상과 포즈 데이터를 사용하여 물체를 탐지하고,
        카메라 오프셋을 적용한 로봇 베이스 기준의 cm 좌표를 반환합니다.
        """
        # 1. 영상, 깊이, 로봇 포즈가 한 세트로 묶인 동기화 패키지를 획득합니다.
        packet = self.driver.get_synced_packet()
        if not packet:
            return []

        color_frame = packet["color"]
        depth_frame = packet["depth"]
        # 영상이 촬영된 시점의 로봇 위치 정보입니다.
        captured_pose = packet["captured_pose"]

        # 2. YOLO 엔진을 사용하여 영상 내 객체의 2D 픽셀 좌표를 탐지합니다.
        raw_detections = self.yolo.detect(color_frame)
        
        refined_list = []
        for det in raw_detections:
            u, v = det["pixel_center"]
            
            # 3. 해당 픽셀의 깊이 정보(m)를 가져와 카메라 기준 3D cm 좌표로 변환합니다.
            depth_val = depth_frame[v, u]
            cam_coords = self.driver.pixel_to_cm(u, v, depth_val)
            
            if cam_coords:
                # 4. [핵심] 카메라 오프셋을 적용하여 로봇 베이스 기준 좌표를 산출합니다.
                # 고정 카메라 설정(SIM_OFFSET)에 따라 절대 좌표계로 변환됩니다.
                robot_x = cam_coords[0] + self.offset["x"]
                robot_y = cam_coords[1] + self.offset["y"]
                robot_z = cam_coords[2] + self.offset["z"]
                
                # 5. 탐지 결과와 함께 당시 로봇의 위치(Sync Pose)를 패키징하여 반환합니다.
                # 이를 통해 좌뇌(LLM)가 현재 위치와 목표 위치를 정확히 대조할 수 있습니다.
                refined_list.append({
                    "name": det["name"],
                    "position": {
                        "x": round(robot_x, 2),
                        "y": round(robot_y, 2),
                        "z": round(robot_z, 2)
                    },
                    "sync_pose": captured_pose # 비주얼 서보잉을 위한 동기화 포즈 포함
                })
                
        return refined_list