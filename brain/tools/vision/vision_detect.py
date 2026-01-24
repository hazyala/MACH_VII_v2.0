# brain/tools/vision/vision_detect.py

from langchain_core.tools import tool
from brain.modules.vision.vision_bridge import VisionBridge

@tool
def vision_detect(query: str = "detect") -> str:
    """
    실시간 카메라 영상을 분석하여 감지된 물체들의 이름과 3D 공간 좌표(cm) 리스트를 반환합니다.
    로봇 팔의 작업 반경 내에 있는 물체들을 확인하고 정밀한 위치를 파악할 때 사용합니다.
    
    Args:
        query (str): 탐지 작업 수행 시 참고할 질의어 (기본값: "detect")
    """
    try:
        # 비전 브릿지 객체를 생성하여 현재 환경(시뮬레이션/실물)에 맞는 데이터를 요청합니다.
        vision_bridge = VisionBridge()
        
        # 브릿지를 통해 YOLO 탐지 및 칼만 필터가 적용된 정제된 3D 좌표 리스트를 가져옵니다.
        # 내부적으로 core 레이어의 드라이버와 modules 레이어의 알고리즘이 연동됩니다.
        detected_items = vision_bridge.get_refined_detections()
        
        if not detected_items:
            return "[RESULT] 현재 시야에서 감지된 물체가 없습니다."

        # 에이전트(좌뇌)가 사고 계획을 세울 수 있도록 결과를 문자열 형식으로 정제합니다.
        # 모든 좌표 단위는 cm이며, 소수점 첫째 자리까지 표시합니다.
        output_text = "[SUCCESS] 물체 탐지 결과 보고:\n"
        for item in detected_items:
            name = item.get("name", "알 수 없음")
            pos = item.get("position", {"x": 0.0, "y": 0.0, "z": 0.0})
            output_text += f"- {name}: (x={pos['x']:.1f}, y={pos['y']:.1f}, z={pos['z']:.1f}) cm\n"
            
        return output_text

    except Exception as e:
        # 도구 실행 중 발생한 예외 상황을 기록하고 에러 메시지를 반환합니다.
        return f"[ERROR] 비전 시스템 구동 중 기술적 오류가 발생했습니다: {str(e)}"