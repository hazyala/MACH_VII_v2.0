import cv2
import numpy as np
import torch
from ultralytics import YOLO
from shared.filters import KalmanFilter

class YoloDetector:
    """
    YOLOv11s를 사용하여 물체를 탐지하고 칼만 필터로 궤적을 다듬는 도구입니다.
    """

    def __init__(self, model_path: str):
        """
        모델 로드 및 연산 장치(GPU/CPU) 설정을 수행합니다.
        """
        # 장치 설정: CUDA(NVIDIA GPU)가 있으면 사용하고, 없으면 CPU를 사용합니다.
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        
        # 모델 로드
        self.model = YOLO(model_path).to(self.device)
        
        # 좌표 정제를 위한 칼만 필터 초기화
        self.filter_x = KalmanFilter()
        self.filter_y = KalmanFilter()
        
        # 물체 소실 감지를 위한 카운터
        self.lost_frames = 0

    def detect_and_filter(self, frame):
        """
        영상을 분석하여 물체 정보와 필터링된 좌표를 반환합니다.
        """
        # 1. YOLO 추론 (yolo11s 모델 사용)
        results = self.model(frame, verbose=False, conf=0.5)  # 신뢰도 0.5 이상만 탐지
        annotated_frame = results[0].plot()
        
        detection_info = {
            "name": None,
            "confidence": 0.0,
            "coords": None
        }

        # 2. 물체가 감지되었을 때 처리
        if len(results[0].boxes) > 0:
            self.lost_frames = 0
            box = results[0].boxes[0]
            
            # 클래스 이름과 신뢰도를 가져옵니다.
            cls_id = int(box.cls[0])
            detection_info["name"] = self.model.names[cls_id]
            detection_info["confidence"] = float(box.conf[0])
            
            # 중심 좌표 추출 (xywh 방식)
            xywh = box.xywh[0].cpu().numpy()
            raw_x, raw_y = xywh[0], xywh[1]

            # 3. 칼만 필터 적용
            clean_x = self.filter_x.update(raw_x)
            clean_y = self.filter_y.update(raw_y)
            detection_info["coords"] = [clean_x, clean_y]

            # 필터링된 좌표 시각화
            cv2.circle(annotated_frame, (int(clean_x), int(clean_y)), 7, (0, 255, 0), -1)
        else:
            # 물체를 놓쳤을 때 필터 초기화 (연속 30프레임 이상 소실 시)
            self.lost_frames += 1
            if self.lost_frames > 30:
                self.filter_x.reset()
                self.filter_y.reset()

        return annotated_frame, detection_info