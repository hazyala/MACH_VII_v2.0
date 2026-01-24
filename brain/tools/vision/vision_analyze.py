# brain/tools/vision/vision_analyze.py

import base64
import requests
import cv2
from langchain_core.tools import tool
from brain.modules.vision.vision_bridge import VisionBridge
from shared.config import GlobalConfig

@tool
def vision_analyze(query: str) -> str:
    """
    VLM(Vision-Language Model)을 사용하여 현재 카메라 영상의 상세 내용을 분석합니다.
    객체의 색상, 재질, 텍스트, 또는 YOLO가 인식하지 못하는 복잡한 상황을 파악할 때 사용합니다.
    
    Args:
        query (str): 이미지 분석을 위한 자연어 질문 (예: "종이컵 안에 무엇이 들어있어?")
    """
    try:
        # 1. 비전 브릿지를 통해 현재 활성화된 드라이버(가상/실물)로부터 최신 프레임을 가져옵니다.
        vision_bridge = VisionBridge()
        frame_data = vision_bridge.get_raw_frame()
        
        if frame_data is None or "color" not in frame_data:
            return "[RESULT] 분석할 영상을 획득하지 못했습니다."

        # 2. 분석 효율을 위해 이미지 크기를 조정하고 JPG로 인코딩합니다.
        resized_frame = cv2.resize(frame_data["color"], (320, 240))
        _, buffer = cv2.imencode('.jpg', resized_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        image_base64 = base64.b64encode(buffer).decode('utf-8')

        # 3. 전역 설정에 정의된 VLM 서버 주소와 모델(Gemma3)을 사용하여 분석을 요청합니다.
        #
        vlm_endpoint = "http://ollama.aikopo.net/api/generate"
        payload = {
            "model": "gemma3:27b",
            "prompt": query,
            "images": [image_base64],
            "stream": False
        }

        response = requests.post(vlm_endpoint, json=payload, timeout=60)
        
        if response.status_code == 200:
            analysis_result = response.json().get('response', '분석 결과가 비어 있습니다.')
            return f"[SUCCESS] 시각 분석 결과:\n{analysis_result}"
        else:
            return f"[FAILURE] VLM 서버 응답 오류 (코드: {response.status_code})"

    except Exception as e:
        # 시스템 오류 발생 시 상세 내용을 기록하고 에러 메시지를 반환합니다.
        return f"[ERROR] VLM 분석 도구 실행 중 오류 발생: {str(e)}"