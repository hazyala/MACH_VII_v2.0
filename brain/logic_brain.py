import time
import threading
import uuid
import asyncio
import re
from typing import Dict, Any

from shared.config import GlobalConfig
from shared.state_broadcaster import broadcaster
from expression.emotion_controller import emotion_controller
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

class UserStopException(BaseException):
    pass

class AgentBroadcasterCallback(BaseCallbackHandler):
    """
    LangChain의 사고 과정(Thought)을 Broadcaster로 송출하고 파이프라인을 트리거하는 콜백 클래스입니다.
    
    작동 원리:
    1. LLM이 도구를 선택하거나 답변을 생성할 때마다 이 클래스의 메서드들이 호출됩니다.
    2. 생성된 생각(Text)이나 도구 사용(Action) 정보를 'agent_thought' 채널로 실시간 방송합니다.
    3. 에이전트가 최종 답변을 내놓으면(on_agent_finish), 그 결과를 파이프라인의 입력으로 전달하여 실제 물리 행동을 유도합니다.
    """
    def __init__(self, logic_brain_instance):
        self.brain = logic_brain_instance
        self.tool_used = False # [Double Action Prevention]

    def _check_stop(self):
        if self.brain.stop_token.is_set():
            raise UserStopException("사용자에 의해 중단되었습니다.")

    def on_chain_start(self, serialized, inputs, **kwargs):
        self._check_stop()
        self.tool_used = False # 체인 시작 시 초기화
        broadcaster.publish("agent_thought", ">>>> 생각 시작...")

    def _parse_and_trigger_emotion(self, text: str) -> str:
        """
        텍스트에서 <<EMOTION:preset>> 태그를 찾아 감정 이벤트를 발생시키고,
        태그가 제거된 텍스트를 반환합니다.
        """
        from brain.emotion_brain import emotion_brain
        
        pattern = r"<<EMOTION:(\w+)>>"
        
        matches = re.finditer(pattern, text)
        for match in matches:
            preset_id = match.group(1).lower()
            
            # 1. [Emotion Pulse] 즉시 전파 (Frontend Animation)
            emotion_controller.broadcast_emotion_event(preset_id, weight=1.0, duration=5.0)
            
            # 2. [Emotion State] Brain에 오버라이드 등록 (Sustained Vector)
            emotion_brain.set_emotional_override(preset_id, duration=5.0)
            
        # 태그 제거
        cleaned_text = re.sub(pattern, "", text)
        return cleaned_text

    def on_text(self, text, **kwargs):
        self._check_stop()
        # [Universal Tag Parsing] '생각(Thought)' 중에도 감정 태그가 있으면 즉시 반영
        # 하지만 on_text는 파편화된 토큰일 수 있으므로 주의가 필요함.
        # LangChain의 on_text는 보통 "Thought: " 같은 prefix나 tool output 등을 줍니다.
        # 여기서는 전체 문맥을 잡기 어려우므로, 간단한 태그만 파싱합니다.
        self._parse_and_trigger_emotion(text)
        pass 


    def on_agent_action(self, action, **kwargs):
        self._check_stop()
        broadcaster.publish("agent_thought", f"[도구 사용] {action.tool}: {action.tool_input}")
        
        # [Double Action Prevention]
        if action.tool in ["robot_action", "grasp_object", "vision_analyze"]:
            self.tool_used = True

    def on_tool_end(self, output, **kwargs):
        self._check_stop()

    def on_agent_finish(self, finish, **kwargs):
        self._check_stop()
        # 1. [핵심] 7-Layer 파이프라인 실행 트리거 (Layer 3: Brain -> Layer 4: Strategy ...)
        # LLM이 도출한 최종 의도(Intent)를 문자열에서 열거형(Enum)으로 변환하여 시스템 흐름에 태웁니다.
        # 이 시점부터 에이전트의 사고가 물리적 행동 계획으로 구체화됩니다.
        intent_raw = finish.return_values.get("output", "IDLE")
        
        # [Universal Tag Parsing] 최종 답변(Final Answer)에서 감정 태그 파싱 및 실행
        # 로직: 태그는 감정 표현으로 승화시키고, 사용자에게 보이는 텍스트에서는 지운다.
        cleaned_intent_raw = self._parse_and_trigger_emotion(intent_raw)

        # [Double Action Prevention] 이미 도구로 로봇을 제어했다면, 답변에서 의도를 또 추출하지 않음.
        if self.tool_used:
             broadcaster.publish("agent_thought", "[System] 도구 사용 감지로 인해 implicit intent 생략됨.")
             intent_enum = ActionIntent.IDLE
        else:
             intent_enum = ActionIntent.from_str(cleaned_intent_raw)
             pipeline.process_brain_intent(intent_enum)
        
        # 2. 사용자 통보 (태그가 제거된 깔끔한 텍스트)
        broadcaster.publish("agent_thought", f"[최종 판단] {intent_enum.name} ({cleaned_intent_raw[:30]}...)")
        broadcaster.publish("agent_thought", "<<<< 생각 종료.")
        
        # 원본 output 수정 (LogicBrain의 execute_task에서 사용될 값)
        finish.return_values["output"] = cleaned_intent_raw

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
                temperature=0.1
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

        # 2. 메모리 초기화 (단순 대화 맥락 유지용)
        # ConversationBufferMemory: 대화의 이력을 버퍼에 저장하여 LLM이 이전 대화 내용을 기억하게 합니다.
        # 주의: 이것은 단기 메모리(Session Memory)이며, FalkorDB를 이용한 장기 기억(Long-term Memory)과는 다릅니다.
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="output"
        )
        
        if self.llm is None:
            logging.error("[Brain] LLM이 유효하지 않아 AgentExecutor를 초기화할 수 없습니다.")
            self.agent_executor = None
        else:
            try:
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
                        # "prefix": SYSTEM_INSTRUCTION, # [Safety] 복구: 이전 안정성 확보를 위해 커스텀 프롬프트 비활성화
                        "memory_prompts": [MessagesPlaceholder(variable_name="chat_history")], # 대화 내역 주입
                        "input_variables": ["input", "agent_scratchpad", "chat_history"] # 랭체인 필수 입력 변수
                    }
                )
            except Exception as e:
                logging.error(f"[Brain] AgentExecutor 초기화 실패: {e}")
                self.agent_executor = None
        
        broadcaster.log_chat("bot", "MACH-VII 두뇌(Brain)가 활성화되었습니다.")

    def stop_agent(self):
        """에이전트 사고 강제 중단"""
        print("[Brain] 에이전트 논리를 중단합니다...")
        self.stop_token.set()

    async def execute_task(self, task_command: str):
        """
        비동기적으로 에이전트 사고 루프를 실행합니다. 
        메인 스레드(FastAPI 서버)를 차단하지 않기 위해 asyncio.get_event_loop().run_in_executor를 사용합니다.
        
        Args:
            task_command (str): 사용자의 자연어 명령 (예: "오리를 집어줘")
        """
        self.stop_token.clear() # 시작 시 토큰 초기화
        
        broadcaster.log_chat("user", f"명령: {task_command}")
        broadcaster.publish("agent_state", "THINKING")
        
        try:
            loop = asyncio.get_event_loop()
            # self.stop_token을 공유하기 위해 self를 넘김
            callbacks = [AgentBroadcasterCallback(self)]
            
            # [Context Injection] 현재 시각적 인지(Perception) 상태 주입
            # 에이전트가 "지금 뭐가 보여?"라고 물어보지 않아도 알 수 있도록,
            # 현재 시스템 상태(system_state)에 저장된 감지된 물체 목록을 프롬프트에 미리 포함시킵니다.
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
            
            # [Context Injection] 감정(Emotion) 상태 주입 (Phase 2)
            # LLM이 자신의 감정 상태를 인지하고 페르소나에 반영하도록 합니다.
            # emotion_controller는 background에서 system_state를 계속 업데이트하고 있습니다.
            from expression.emotion_controller import emotion_controller
            current_emotion = system_state.emotion
            preset_id = emotion_controller.get_closest_preset()
            
            emotion_str = (
                f"\n[현재 감정]: {preset_id.upper()} "
                f"(Focus: {current_emotion.focus:.2f}, "
                f"Confidence: {current_emotion.confidence:.2f}, "
                f"Frustration: {current_emotion.frustration:.2f})"
            )
            
            # 입력 메시지에 컨텍스트 추가 (시야 정보 + 감정 정보)
            full_input = f"{task_command}{context_str}{emotion_str}"
            
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