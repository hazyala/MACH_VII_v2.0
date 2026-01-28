from langchain_core.tools import tool, Tool
import requests
import json
from state.system_state import system_state
from shared.state_broadcaster import broadcaster
from memory.falkordb_manager import memory_manager

class ToolsFactory:
    def __init__(self):
        pass

    def get_vision_detect_tool(self):
        @tool
        def vision_detect(query: str = ""):
            """현재 카메라에 보이는 물체의 목록과 위치를 파악할 때 사용합니다. 입력값은 비워두어도 됩니다."""
            perception = system_state.perception_data
            objects = perception.get("detected_objects", [])
            msg = f"현재 감지된 객체 ({len(objects)}개):\n"
            if not objects:
                return "아무것도 감지되지 않았습니다."
            
            for obj in objects:
                bbox = obj.get("bbox")
                cx = (bbox[0] + bbox[2]) // 2
                cy = (bbox[1] + bbox[3]) // 2
                msg += f"- {obj['label']} (신뢰도 {obj['confidence']:.2f}) 위치: ({cx}, {cy})\n"
            return msg
        return vision_detect

    def get_vision_analyze_tool(self):
        @tool
        def vision_analyze(question: str):
            """객체 탐지로 알 수 없는 구체적인 시각적 특징(색상, 표정, 텍스트 등)을 물어볼 때 사용합니다."""
            b64_image = system_state.last_frame_base64
            if not b64_image:
                return "오류: 분석할 이미지가 없습니다. (카메라 연결 안됨)"
            
            try:
                payload = {
                    "model": "llava", 
                    "prompt": question,
                    "images": [b64_image],
                    "stream": False
                }
                response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=30)
                if response.status_code == 200:
                    res_json = response.json()
                    return f"[시각 분석 결과]: {res_json.get('response', '응답 없음')}"
                else:
                    return f"VLM 서버 오류: {response.status_code} - {response.text}"
            except Exception as e:
                return f"시각 분석 중 오류 발생: {str(e)}"
        return vision_analyze

    def get_action_tool(self):
        @tool
        def action_emit(intent: str):
            """로봇에게 물리적인 행동을 지시하거나 모드를 변경할 때 사용합니다. 예: '인사해라', '잡아라'"""
            system_state.current_intent = intent
            broadcaster.publish("action_intent", intent)
            broadcaster.publish("agent_thought", f"[Action] 의도 전파됨: {intent}")
            return f"행동 의도 '{intent}'를 시스템에 전달했습니다. 하드웨어가 이를 수행할 것입니다."
        return action_emit

    def get_memory_search_tool(self):
        @tool
        def memory_search(query: str):
            """과거의 기억이나 정보를 찾아야 할 때 사용합니다."""
            return "기억 시스템: (아직 연결되지 않음)"
        return memory_search

tools_factory = ToolsFactory()
ALL_TOOLS = [
    tools_factory.get_vision_detect_tool(),
    tools_factory.get_vision_analyze_tool(),
    tools_factory.get_action_tool(),
    tools_factory.get_memory_search_tool()
]
