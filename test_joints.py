"""
DOFBOT 로봇 조인트 각도 테스트 스크립트

현재 조인트 각도를 조회하고 수직 일직선 기본 자세를 찾습니다.
"""

import logging
import time
import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

from shared.config import GlobalConfig
from embodiment.dofbot_robot import DofbotRobot

print("=" * 60)
print("  DOFBOT 조인트 각도 테스트")
print("=" * 60)

# 로봇 연결
print(f"\n[로봇] {GlobalConfig.DOFBOT_SERVER_URL} 연결 시도...")
robot = DofbotRobot()
time.sleep(2.0)


if not robot.connected:
    print("[ERROR] 로봇 연결 실패")
    print("DOFBOT 서버가 실행 중인지 확인하세요:")
    print("  cd 참고/DOFBOT_ROBOT_ARM-main && python main.py")
    sys.exit(1)

print("[OK] 로봇 연결 성공\n")

# 현재 상태 조회 루프
print("=" * 60)
print("현재 로봇 상태 조회 (수동 조작용)")
print("=" * 60)
print("\n로봇을 수동으로 움직인 후 Enter를 눌러 현재 상태를 조회하세요.")
print("종료하려면 'q'를 입력하고 Enter를 누르세요.\n")

while True:
    user_input = input("조회하려면 Enter, 종료하려면 'q': ").strip().lower()
    
    if user_input == 'q':
        print("\n프로그램을 종료합니다.")
        break
    
    # 현재 상태 조회
    pose = robot.get_current_pose()
    
    print("\n" + "=" * 60)
    print(f"위치 (cm):")
    print(f"  x = {pose['position']['x']:.2f}")
    print(f"  y = {pose['position']['y']:.2f}")
    print(f"  z = {pose['position']['z']:.2f}")
    
    print(f"\n관절 각도 (degrees):")
    joints = pose['joints']
    for i, angle in enumerate(joints):
        print(f"  Joint {i+1}: {angle:.1f}°")
    
    # 관절각을 리스트로 출력 (복사하기 쉽게)
    print(f"\n관절각 리스트 (복사용):")
    print(f"  {[round(j, 1) for j in joints]}")
    print("=" * 60 + "\n")

print("\n" + "=" * 60)
print("테스트 완료")
print("=" * 60)

# 정리
robot.disconnect()
