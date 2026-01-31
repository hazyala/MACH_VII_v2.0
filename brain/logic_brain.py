import time
import threading
import uuid
import asyncio
from typing import Dict, Any

from shared.config import GlobalConfig
from shared.state_broadcaster import broadcaster
from .tools import ALL_TOOLS
from .prompts import SYSTEM_INSTRUCTION
from memory.falkordb_manager import memory_manager

# LangChain Imports
from langchain_community.chat_models import ChatOllama
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import MessagesPlaceholder
from langchain.callbacks.base import BaseCallbackHandler

from shared.intents import ActionIntent
from shared.pipeline import pipeline

class UserStopException(Exception):
    pass

class AgentBroadcasterCallback(BaseCallbackHandler):
    """LangChain의 사고 과정(Thought)을 Broadcaster로 송출하고 파이프라인을 트리거하는 콜백"""
    def __init__(self, logic_brain_instance):
        self.brain = logic_brain_instance

    def _check_stop(self):
        if self.brain.stop_token.is_set():
            raise UserStopException("사용자에 의해 중단되었습니다.")

    def on_chain_start(self, serialized, inputs, **kwargs):
        self._check_stop()
        broadcaster.publish("agent_thought", ">>>> 생각 시작...")

    def on_text(self, text, **kwargs):
        self._check_stop()
        pass # 너무 잡다한 텍스트 제외

    def on_agent_action(self, action, **kwargs):
        self._check_stop()
        broadcaster.publish("agent_thought", f"[도구 사용] {action.tool}: {action.tool_input}")

    def on_tool_end(self, output, **kwargs):
        self._check_stop()

    def on_agent_finish(self, finish, **kwargs):
        self._check_stop()
        # 1. [핵심] 파이프라인 실행 (Layer 3 -> Layer 4 -> ... -> Layer 7)
        intent_raw = finish.return_values.get("output", "IDLE")
        
        # 파이프라인 내부에서 이미 변환하지만, 로깅을 위해 여기서도 변환
        intent_enum = ActionIntent.from_str(intent_raw)
        pipeline.process_brain_intent(intent_enum)
        
        # 2. UI 통보
        broadcaster.publish("agent_thought", f"[최종 판단] {intent_enum.name} ({intent_raw[:30]}...)")
        broadcaster.publish("agent_thought", "<<<< 생각 종료.")

from strategy.strategy_manager import strategy_manager

class LogicBrain:
    """
    LangChain 기반의 메인 논리 에이전트 클래스입니다.
    """
    def __init__(self):
        # 전략적 상태는 이제 StrategyManager가 전담합니다.
        self.stop_token = threading.Event()
        
        # 1. LLM 초기화 (Ollama)
        try:
            self.llm = ChatOllama(
                model=GlobalConfig.VLM_MODEL, 
                base_url=GlobalConfig.VLM_ENDPOINT.replace("/api/generate", ""), # base_url은 /api/generate 제외
                temperature=0.0
            )
            # 간단한 호출로 연결 테스트
            # self.llm.invoke("test") # 실가동 시에는 생략 가능 (시간 단축)
        except Exception as e:
             print(f"[Brain] 메인 VLM 연결 실패: {e}")
             # Fallback to local Ollama (Llama 3 or similar)
             try:
                 print("[Brain] 로컬 Ollama(llama3)로 전환을 시도합니다...")
                 self.llm = ChatOllama(model="llama3", temperature=0)
             except Exception as fe:
                 print(f"[Brain] 모든 LLM 초기화 실패: {fe}")
                 print("[IMPORTANT] Ollama가 설치되어 있고 모델이 다운로드 되었는지 확인하세요.")
                 # 극단적인 경우 에러를 발생시키지 않고 빈 모델 객체를 유지하거나 더미 클래스 사용
                 self.llm = None

        # 2. 메모리 초기화 (단순화를 위해 ConversationBufferMemory 사용)
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output"
        )
        
        # 3. 에이전트 초기화 (안정성을 위해 initialize_agent 사용)
        from langchain.agents import initialize_agent, AgentType
        
        self.agent_executor = initialize_agent(
            tools=ALL_TOOLS, 
            llm=self.llm, 
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION, 
            verbose=True, 
            handle_parsing_errors=True,
            memory=self.memory,
            max_iterations=15,
            agent_kwargs={
                "prefix": SYSTEM_INSTRUCTION,
                "memory_prompts": [MessagesPlaceholder(variable_name="chat_history")],
                "input_variables": ["input", "agent_scratchpad", "chat_history"]
            }
        )
        
        broadcaster.log_chat("bot", "MACH-VII 두뇌(Brain)가 활성화되었습니다.")

    def stop_agent(self):
        """에이전트 사고 강제 중단"""
        print("[Brain] Stopping Agent Logic...")
        self.stop_token.set()

    async def execute_task(self, task_command: str):
        """
        비동기로 에이전트를 실행합니다. API 스레드를 차단하지 않습니다.
        """
        self.stop_token.clear() # 시작 시 토큰 초기화
        
        broadcaster.log_chat("user", f"명령: {task_command}")
        broadcaster.publish("agent_state", "THINKING")
        
        try:
            loop = asyncio.get_event_loop()
            # self.stop_token을 공유하기 위해 self를 넘김
            callbacks = [AgentBroadcasterCallback(self)]
            
            # [Context Injection] 현재 비전 상태를 입력에 포함
            from state.system_state import system_state
            perception = system_state.perception_data
            
            context_str = ""
            if perception and "detected_objects" in perception:
                objects = perception["detected_objects"]
                if objects:
                    obj_list = [f"- {obj['name']} at ({obj['position']['x']}, {obj['position']['y']}, {obj['position']['z']})" for obj in objects]
                    context_str = "\n\n[현재 시야에 보이는 물체들(실시간 업데이트)]:\n" + "\n".join(obj_list)
                else:
                    context_str = "\n\n[현재 시야]: 물체 없음"
            
            # 입력 메시지에 컨텍스트 추가
            full_input = f"{task_command}{context_str}"
            
            # 동기 함수인 agent_executor.invoke를 비동기로 실행
            response = await loop.run_in_executor(
                None, 
                lambda: self.agent_executor.invoke(
                    {"input": full_input},
                    {"callbacks": callbacks}
                )
            )
            
            output_msg = response.get("output", "응답을 생성하지 못했습니다.")
            broadcaster.log_chat("bot", output_msg)
            broadcaster.publish("agent_state", "IDLE")

        except UserStopException:
            broadcaster.log_chat("bot", "🚨 사용자의 요청으로 생각을 멈췄습니다.")
            broadcaster.publish("agent_state", "IDLE")

        except Exception as e:
            err_msg = f"Brain 오류 발생: {str(e)}"
            print(err_msg)
            broadcaster.log_chat("bot", "오류가 발생하여 생각을 멈췄습니다.")
            broadcaster.publish("agent_state", "ERROR")

# 싱글톤 객체
logic_brain = LogicBrain()