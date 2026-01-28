import cv2
import requests
import json
import threading
import time
import numpy as np
import websocket

# 서버 설정
SERVER_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

class MachTestClient:
    def __init__(self):
        self.running = True
        self.latest_rgb = None
        self.latest_emotion = "IDLE"
        self.thought_log = []
        
    def video_stream_thread(self):
        """MJPEG 스트림을 수신하여 OpenCV 창에 표시합니다."""
        print("[Video] 스트림 수신 시작...")
        cap = cv2.VideoCapture(f"{SERVER_URL}/video/rgb")
        while self.running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue
            
            # 화면 크기 조정
            display_frame = cv2.resize(frame, (640, 480))
            
            # 오버레이 정보 추가 (상태 표시)
            cv2.putText(display_frame, f"Emotion: {self.latest_emotion}", (20, 40), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            cv2.imshow("MACH-VII v2.0 - Vision Feed", display_frame)
            
            # 간단한 '표정' 창 (OpenCV로 도형 그리기)
            self.draw_face()
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.running = False
                break
        cap.release()
        cv2.destroyAllWindows()

    def draw_face(self):
        """현재 감정 상태에 기반한 간단한 표정을 별도 창에 그립니다."""
        face_img = np.zeros((300, 300, 3), dtype=np.uint8)
        color = (255, 255, 255) # White
        
        # 감정에 다른 색상/모양 (예시)
        if self.latest_emotion == "HAPPY": color = (0, 255, 255)
        elif self.latest_emotion == "SAD": color = (255, 0, 0)
        elif self.latest_emotion == "ANGRY": color = (0, 0, 255)
        
        # 눈 그리기
        cv2.circle(face_img, (100, 100), 20, color, -1)
        cv2.circle(face_img, (200, 100), 20, color, -1)
        
        # 입 그리기 (상태에 따라 모양 변경 가능)
        cv2.line(face_img, (100, 200), (200, 200), color, 5)
        
        cv2.imshow("MACH-VII v2.0 - Face", face_img)

    def ws_listener_thread(self):
        """WebSocket을 통해 브레인의 사고 과정 및 상태 정보를 실시간 수신합니다."""
        def on_message(ws, message):
            data = json.loads(message)
            
            # 감정 업데이트
            new_emotion = data.get("emotion", {}).get("current", "IDLE")
            if new_emotion != self.latest_emotion:
                self.latest_emotion = new_emotion
            
            # 사고(Thought) 및 답변(Bot) 출력
            brain_state = data.get("brain", {})
            chat_history = brain_state.get("chat_history", [])
            
            if chat_history:
                last_msg = chat_history[-1]
                msg_id = last_msg.get("id") or str(last_msg) # 중복 출력 방지용 ID
                
                if not hasattr(self, '_last_msg_id') or self._last_msg_id != msg_id:
                    self._last_msg_id = msg_id
                    role = last_msg.get("role")
                    text = last_msg.get("text")
                    
                    if role == "thought":
                        print(f"\n\033[92m[THOUGHT]\033[0m {text}")
                    elif role == "bot":
                        print(f"\n\033[93m[BOT]\033[0m {text}")
                        # 답변이 오면 다시 프롬프트 출력
                        print("\033[94m[COMMAND]\033[0m >> ", end="", flush=True)

        def on_error(ws, error):
            pass # 조용한 오류 처리

        ws = websocket.WebSocketApp(WS_URL, on_message=on_message, on_error=on_error)
        ws.run_forever()

    def terminal_input_thread(self):
        """사용자로부터 터미널 명령을 입력받아 백엔드로 전송합니다."""
        print("\n" + "="*50)
        print("   MACH-VII v2.0 Terminal Test Client (PyBullet Default)")
        print("   - 'q' 입력 시 종료")
        print("   - 모든 명령과 채팅을 지원합니다.")
        print("="*50 + "\n")
        
        # 시작 시 백엔드 설정을 PyBullet으로 강제 전환
        try:
            requests.post(f"{SERVER_URL}/api/config", params={"camera_source": "PyBullet"})
            print("[System] PyBullet 모드로 초기화되었습니다.")
        except:
            print("[Warning] 서버 연결 실패. 서버가 실행 중인지 확인하세요.")

        while self.running:
            cmd = input("\033[94m[COMMAND]\033[0m >> ")
            if cmd.lower() == 'q':
                self.running = False
                break
            
            if cmd.strip():
                try:
                    requests.post(f"{SERVER_URL}/api/command", params={"command": cmd})
                except Exception as e:
                    print(f"[Error] 전송 실패: {e}")

    def run(self):
        # 3개의 스레드 실행
        t1 = threading.Thread(target=self.video_stream_thread, daemon=True)
        t2 = threading.Thread(target=self.ws_listener_thread, daemon=True)
        
        t1.start()
        t2.start()
        
        # 메인 스레드에서 입력 대기
        self.terminal_input_thread()
        self.running = False
        print("테스트 클라이언트를 종료합니다.")

if __name__ == "__main__":
    client = MachTestClient()
    client.run()
