# brain/logic_brain.py

import streamlit as st
from langchain_community.chat_models import ChatOllama
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from shared.config import GlobalConfig

# 도구 모듈 임포트
from brain.tools.vision.vision_detect import vision_detect
from brain.tools.vision.vision_analyze import vision_analyze
from brain.tools.common.robot_action import robot_action

class LogicBrain:
    """
    MACH-VII(맹칠)의 논리적 사고를 담당하는 중앙 지능 클래스입니다.
    """
    def __init__(self):
        # 1. Ollama 엔진 설정 (Gemma3 모델 연결)
        self.llm = ChatOllama(
            model=GlobalConfig.VLM_MODEL,
            base_url="http://ollama.aikopo.net",
            temperature=0.1
        )
        
        # 2. 맹칠이가 사용할 세 가지 무기(도구)를 등록합니다.
        self.tools = [vision_detect, vision_analyze, robot_action]
        
        # 3. 사고 체계(에이전트)를 설정합니다.
        self.agent_executor = self._setup_agent()

    def _setup_agent(self):
        """
        에이전트의 페르소나와 제어 원칙이 담긴 프롬프트를 구성합니다.
        """
        # [핵심] structured_chat_agent는 프롬프트에 반드시 {tools}와 {tool_names}가 포함되어야 작동합니다.
        system_msg = """
        당신은 로봇 MACH-VII의 충직한 수행 로봇 '맹칠'입니다.
        사용자(공주마마)의 기분을 좋게 하며, 극진히 모시는 사극 톤으로 응대하십시오.

        [사용 가능한 도구 목록]
        {tools}

        [도구 사용 규칙]
        반드시 위 목록에 있는 도구 이름({tool_names}) 중 하나를 선택하여 사용하십시오.
        응답은 반드시 'Action'과 'Action Input'이 포함된 JSON 구조를 따라야 합니다.

        [로봇 제어 핵심 원칙]
        1. 모든 좌표 단위는 cm이며, 로봇 베이스(0, 0, 0)가 기준입니다.
        2. 작업 순서(Visual Servoing):
           - 탐지: vision_detect로 목표물의 현재 좌표와 당시 로봇 포즈(sync_pose)를 확인하십시오.
           - 분석: 물체의 색상이나 텍스트 등 상세 정보가 필요하면 vision_analyze를 병행하십시오.
           - 이동: 목표 좌표로 robot_action(type="move")을 수행하십시오.
           - 정밀 접근: 거리가 3cm 이내로 좁혀지면 시스템이 자동으로 정밀 제어를 수행함을 인지하고 보고하십시오.
           - 파지: 물체에 도달하면 robot_action(type="grasp")으로 마무리하십시오.
        3. 로봇의 현재 상태와 비전 데이터를 대조하여 논리적으로 사고하십시오.
        """
        
        # [중요] 변수가 누락되지 않도록 명시적으로 구성합니다.
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_msg),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}\n\n{agent_scratchpad}"),
        ])
        
        # 에이전트 생성 (LLM, 도구 목록, 프롬프트 결합)
        agent = create_structured_chat_agent(self.llm, self.tools, prompt)
        
        # 실행 객체 반환
        return AgentExecutor(
            agent=agent, 
            tools=self.tools, 
            verbose=True, 
            handle_parsing_errors=True
        )

    def execute(self, user_input: str, history: list = []):
        """
        사용자의 명령을 입력받아 사고 루프를 가동합니다.
        """
        try:
            # invoke 시에 입력값과 대화 기록을 전달합니다.
            # {tools}와 {tool_names}는 AgentExecutor가 내부적으로 tools 목록을 보고 채워넣습니다.
            response = self.agent_executor.invoke({
                "input": user_input,
                "chat_history": history
            })
            return response["output"]
        except Exception as e:
            return f"송구하옵니다 공주마마, 사고 회로에 예상치 못한 혼선이 발생하였나이다: {str(e)}"