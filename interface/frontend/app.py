# interface/frontend/app.py

import sys
import os
from pathlib import Path
import streamlit as st

# 시스템 경로 등록: 프로젝트 루트 폴더를 인식하도록 설정
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from brain.logic_brain import LogicBrain

def main():
    # 조종석 레이아웃 및 제목 설정
    st.set_page_config(
        page_title="MACH-VII 조종석",
        layout="wide"
    )

    st.title("🏯 MACH-VII (맹칠) 중앙 제어 조종석")
    
    # 지능 엔진(LogicBrain) 세션 상태 초기화
    if "logic_brain" not in st.session_state:
        with st.spinner("맹칠이의 사고 회로를 정렬하고 있사옵니다..."):
            try:
                st.session_state.logic_brain = LogicBrain()
            except Exception as e:
                st.error(f"지능 엔진 연결에 실패하였나이다: {str(e)}")
                return

    # 대화 기록 세션 상태 초기화
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # [1] 화면 분할: 왼쪽은 비전 데이터, 오른쪽은 대화창
    col_vision, col_chat = st.columns([1.5, 1])

    with col_vision:
        st.subheader("🎥 실시간 비전 데이터")
        vision_placeholder = st.empty()
        
        # 이전 오류를 수정한 호환성 있는 이미지 출력 방식
        vision_placeholder.image(
            "https://via.placeholder.com/640x480.png?text=Waiting+for+Vision+Stream...",
            use_column_width=True,
            caption="현재 비전 전령이 대기 중이옵니다."
        )
        
        st.divider()
        st.subheader("📊 로봇 상태 정보 (Telemetry)")
        stat_col1, stat_col2 = st.columns(2)
        stat_col1.metric("현재 좌표 (X, Y, Z)", "0.0, 0.0, 0.0", "cm")
        stat_col2.metric("파지 상태", "Open", "Grip")

    with col_chat:
        st.subheader("💬 맹칠이와의 대화")
        # 대화 내역 출력 루프 (기둥 안에서 메시지만 보여줍니다)
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # [2] 입력창은 기둥(with) 밖, 즉 성곽의 가장 아래 마당에 배치합니다.
    # 이것이 스트림릿의 엄격한 법도이옵니다.
    if user_prompt := st.chat_input("공주마마, 무엇을 명하시겠사옵니까?"):
        # 사용자 명령 기록
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        
        # 화면 새로고침 시 메시지가 바로 보이도록 처리
        with col_chat:
            with st.chat_message("user"):
                st.markdown(user_prompt)

            with st.chat_message("assistant"):
                # 이전 대화 기록 전달
                chat_history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                
                with st.spinner("맹칠이 사고 중..."):
                    ai_response = st.session_state.logic_brain.execute(user_prompt, chat_history)
                
                st.markdown(ai_response)
                # 맹칠이의 답변 기록
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
        
        # 입력 후 화면 갱신을 유도합니다.
        st.rerun()

if __name__ == "__main__":
    main()