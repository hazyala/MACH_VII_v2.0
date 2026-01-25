# brain/logic_brain.py

from langchain_community.chat_models import ChatOllama
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from shared.config import GlobalConfig

# 비전 및 로봇 제어 도구들을 임포트합니다.
from brain.tools.vision.vision_detect import vision_detect
from brain.tools.vision.vision_analyze import vision_analyze
from brain.tools.common.robot_action import robot_action

class LogicBrain:
    """
    MACH-VII(맹칠)의 논리 지능을 담당하며 터미널 기반 입출력에 최적화되어 있습니다.
    """
    def __init__(self):
        # 1. Ollama 엔진 설정 (Gemma3 모델 연결)
        self.llm = ChatOllama(
            model=GlobalConfig.VLM_MODEL,
            base_url="http://ollama.aikopo.net",
            temperature=0.1
        )
        
        # 2. 사용할 도구 목록 정의
        self.tools = [vision_detect, vision_analyze, robot_action]
        
        # 3. 사고 체계(에이전트) 설정
        self.agent_executor = self._setup_agent()

    def _setup_agent(self):
        """
        에이전트가 도구 호출 시 불필요한 텍스트를 섞지 않도록 엄격한 프롬프트를 구성합니다.
        """
        system_msg = """
        당신은 로봇 MACH-VII의 수행 로봇 '맹칠'입니다.
        사용자(공주마마)를 극진히 모시는 사극 톤으로 답변하십시오.

        [중요 지침]
        1. 도구를 호출할 때는 절대 사설이나 인삿말을 붙이지 말고 오직 JSON 형식의 Action과 Action Input만 출력하십시오.
        2. 모든 사고가 끝난 후 'Final Answer'에서만 공주마마께 정중히 사극 톤으로 결과를 보고하십시오.

        [사용 가능한 도구 목록]
        {tools}

        [도구 사용 규칙]
        반드시 목록에 있는 이름({tool_names}) 중 하나를 선택하십시오.
        결과가 없더라도 아는 범위 내에서 최종 답변을 작성하십시오.
        """
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_msg),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}\n\n{agent_scratchpad}"),
        ])
        
        # 구조화된 대화형 에이전트 생성
        agent = create_structured_chat_agent(self.llm, self.tools, prompt)
        
        # 실행기 설정 (verbose=True로 설정하여 터미널에서 생각 과정을 실시간으로 노출)
        return AgentExecutor(
            agent=agent, 
            tools=self.tools, 
            verbose=True, 
            handle_parsing_errors="입력 형식이 JSON이 아닙니다. Action과 Action Input 형식을 엄수하십시오.",
            max_iterations=5
        )

    def execute(self, user_input, history):
        """
        터미널로부터 입력을 받아 에이전트 루프를 실행합니다.
        """
        try:
            response = self.agent_executor.invoke({
                "input": user_input,
                "chat_history": history
            })
            return response["output"]
        except Exception as e:
            return f"송구하옵니다 공주마마, 사고 회로에 혼선이 발생하였나이다: {str(e)}"