import base64
import requests
import cv2
import streamlit as st
from langchain_core.tools import tool
from brain.modules.vision.vision_bridge import VisionBridge
from shared.config import GlobalConfig

@tool
def vision_analyze(query: str) -> str:
    """
    VLM(Vision-Language Model)을 사용하여 현재 카메라 영상의 상세 내용을 분석합니다.
    물체의 색상, 재질, 텍스트 또는 복잡한 상황을 파악할 때 사용합니다.
    """
    try:
        # 비전 브릿지에서 VLM 분석에 사용할 원본 RGB 프레임을 획득합니다.
        #
        bridge = VisionBridge()
        frame_data = bridge.get_raw_frame()
        
        if frame_data is None or "color" not in frame_data:
            return "[RESULT] 분석할 영상을 획득하지 못했습니다."

        # 분석 서버 전송을 위해 이미지를 최적화하고 Base64로 인코딩합니다.
        color_frame = frame_data["color"]
        resized_image = cv2.resize(color_frame, (320, 240))
        _, buffer = cv2.imencode('.jpg', resized_image, [cv2.IMWRITE_JPEG_QUALITY, 85])
        image_base64 = base64.b64encode(buffer).decode('utf-8')

        # 전역 설정에 정의된 VLM 서버(Gemma3)에 분석을 요청합니다.
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
            result = response.json().get('response', '분석 결과가 없습니다.')
            return f"[SUCCESS] 시각 분석 보고:\n{result}"
        else:
            return f"[FAILURE] 서버 응답 오류 (코드: {response.status_code})"

    except Exception as e:
        return f"[ERROR] VLM 분석 도구 실행 오류: {str(e)}"