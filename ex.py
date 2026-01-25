# find_camera.py
import cv2

def scan_cameras():
    print("[탐색] 사용 가능한 카메라 번호를 찾는 중이옵니다...")
    valid_indices = []
    for i in range(10):  # 0번부터 9번까지 수색
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"✅ 번호 {i}번: 카메라 전령을 찾았나이다!")
            valid_indices.append(i)
            cap.release()
    return valid_indices

if __name__ == "__main__":
    indices = scan_cameras()
    if not indices:
        print("❌ 소생이 온 성곽을 뒤졌으나 카메라를 한 대도 찾지 못했나이다. 연결을 확인하소서!")