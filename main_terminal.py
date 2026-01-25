# main_terminal.py

import cv2
import numpy as np
import threading
import sys
import os
from pathlib import Path

# [1] 시스템 경로 설정: 프로젝트 루트를 인식시켜 모든 모듈을 불러올 수 있게 합니다.
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# [2] 처소 주소(Package Path)를 명시하여 전령을 깨웁니다.
try:
    from brain.logic_brain import LogicBrain
    from interface.backend.pybullet_client import PybulletClient
except ImportError as e:
    print(f"[경보] 전령을 부르는 데 실패하였나이다. 경로를 확인하소서: {e}")
    sys.exit(1)

def start_vision_monitor(client: PybulletClient):
    """
    서버로부터 RGB와 Depth 데이터를 실시간으로 수혈받아 나란히 출력합니다.
    """
    client.connect() # 서버 연결 시도
    print("[비전] 파이불렛 서버의 눈을 통해 전장을 감시하옵니다.")

    while True:
        try:
            # 서버로부터 영상 및 깊이 데이터 획득
            rgb_view = client.get_rgb_frame()
            depth_data = client.get_depth_frame()

            if rgb_view is None:
                continue

            # 깊이 데이터 시각화: 수치를 색상(Jet 컬러맵)으로 변환하여 거리감을 부여합니다.
            if depth_data is not None:
                # 0~255 범위로 정규화 후 컬러맵 적용
                depth_norm = cv2.normalize(depth_data, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
                depth_colored = cv2.applyColorMap(depth_norm, cv2.COLORMAP_JET)
            else:
                depth_colored = np.zeros_like(rgb_view)

            # RGB와 Depth 영상을 가로로 나란히 결합합니다.
            combined_frame = np.hstack((rgb_view, depth_colored))

            # 모니터 창에 상태 표시
            cv2.putText(combined_frame, "MACH-VII v2.0 DUAL VISION (RGB | DEPTH)", (20, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # 독립된 OpenCV 창 띄우기
            cv2.imshow("MACH-VII VISION MONITOR", combined_frame)

            # 'q' 키를 누르면 비전 창만 종료합니다.
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        except Exception as e:
            print(f"[오류] 비전 스트림 중단: {e}")
            break

    cv2.destroyAllWindows()

def main():
    """
    터미널 기반 메인 명령 전달 루프입니다.
    """
    print("="*60)
    print("🏯 MACH-VII (맹칠) 터미널 제어소 - v2.0 실전형")
    print("="*60)

    # 지능 엔진 및 서버 클라이언트 초기화
    brain = LogicBrain()
    client = PybulletClient()
    chat_history = []

    # 비전 모니터링을 별도 스레드(병렬)로 가동합니다.
    vision_thread = threading.Thread(target=start_vision_monitor, args=(client,), daemon=True)
    vision_thread.start()

    print("\n[인사] 맹칠 대령하였나이다! 공주마마, 분부만 내리소서.")
    print("(종료하시려면 'exit'을 입력하시옵소서)\n")

    while True:
        try:
            user_input = input(">> 공주마마: ")
            
            if user_input.lower() in ['exit', 'quit', '종료']:
                print("\n[인사] 맹칠, 이만 물러가옵니다. 성체 만강하소서!")
                break
            
            if not user_input.strip():
                continue

            # 맹칠이의 사고 과정을 터미널에 실시간 로그로 보여주며 실행합니다.
            print("\n[사고] 맹칠이 생각 중...")
            answer = brain.execute(user_input, chat_history)
            
            # 대화 기록 유지
            chat_history.append({"role": "user", "content": user_input})
            chat_history.append({"role": "assistant", "content": answer})
            
            print(f"\n🤖 맹칠: {answer}\n")
            print("-" * 40)

        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()