# vision_debug.py
"""
비전 시스템 디버그 도구
- YOLO 바운딩 박스 실시간 표시
- 칼만 필터 적용 전/후 좌표 비교
- FPS 표시
"""

import cv2
import numpy as np
import time
import logging
from sensor.vision_bridge import VisionBridge
from sensor.yolo_detector import YoloDetector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class VisionDebugger:
    def __init__(self):
        self.vision = VisionBridge()
        self.yolo = YoloDetector()
        self.fps = 0
        self.last_time = time.time()
        
    def draw_detections(self, frame, detections, refined_detections):
        """
        프레임에 YOLO 탐지 결과와 칼만 필터 적용 후 좌표를 표시합니다.
        
        Args:
            frame: 원본 프레임
            detections: YOLO RAW 탐지 결과 (픽셀 좌표)
            refined_detections: 칼만 필터 + 오프셋 적용 후 (cm 좌표)
        """
        display_frame = frame.copy()
        h, w = frame.shape[:2]
        
        # YOLO 바운딩 박스 그리기
        for det in detections:
            u, v = det["pixel_center"]
            name = det["name"]
            
            # 중심점 표시 (빨간색)
            cv2.circle(display_frame, (u, v), 5, (0, 0, 255), -1)
            cv2.putText(display_frame, f"{name} (RAW)", (u + 10, v), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        # 칼만 필터 적용 후 좌표 표시
        info_y = 30
        for i, refined in enumerate(refined_detections):
            name = refined["name"]
            pos = refined["position"]
            
            # 화면 왼쪽 상단에 정보 표시 (녹색)
            text = f"{name}: ({pos['x']:.1f}, {pos['y']:.1f}, {pos['z']:.1f}) cm"
            cv2.putText(display_frame, text, (10, info_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            info_y += 25
        
        # FPS 표시
        cv2.putText(display_frame, f"FPS: {self.fps:.1f}", (w - 120, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        # 상태 표시
        status = f"Detections: {len(detections)} | Refined: {len(refined_detections)}"
        cv2.putText(display_frame, status, (10, h - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return display_frame
    
    def run(self):
        """디버그 화면 실행"""
        print("=" * 60)
        print("비전 시스템 디버그 모드")
        print("=" * 60)
        print("- YOLO 탐지 결과: 빨간색 점")
        print("- 칼만 필터 적용 후: 녹색 텍스트 (cm 좌표)")
        print("- 'q' 키: 종료")
        print("=" * 60)
        
        cv2.namedWindow("Vision Debug", cv2.WINDOW_AUTOSIZE)
        
        frame_count = 0
        start_time = time.time()
        
        try:
            while True:
                # 1. 원본 프레임 획득
                raw_frame = self.vision.get_raw_frame()
                if raw_frame is None:
                    logging.warning("프레임을 가져올 수 없습니다. 서버 연결을 확인하세요.")
                    time.sleep(0.5)
                    continue
                
                # 2. YOLO 탐지 (RAW)
                yolo_detections = self.yolo.detect(raw_frame)
                
                # 3. 칼만 필터 + 오프셋 적용 (refined)
                refined_detections = self.vision.get_refined_detections()
                
                # 4. 시각화
                display_frame = self.draw_detections(raw_frame, yolo_detections, refined_detections)
                
                # 5. FPS 계산
                frame_count += 1
                elapsed = time.time() - start_time
                if elapsed > 1.0:
                    self.fps = frame_count / elapsed
                    frame_count = 0
                    start_time = time.time()
                
                # 6. 화면 표시
                cv2.imshow("Vision Debug", display_frame)
                
                # 7. 키 입력 확인
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("\n종료합니다...")
                    break
                    
        except KeyboardInterrupt:
            print("\n사용자에 의해 종료되었습니다.")
        finally:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    debugger = VisionDebugger()
    debugger.run()
