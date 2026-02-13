"""
DOFBOT 모든 관절각을 0으로 설정하는 테스트 스크립트
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
print("  DOFBOT 관절각 0으로 설정 테스트")
print("=" * 60)

# 로봇 연결
print(f"\n[로봇] {GlobalConfig.DOFBOT_SERVER_URL} 연결 시도...")
robot = DofbotRobot()
time.sleep(2.0)

if not robot.connected:
    print("[ERROR] 로봇 연결 실패")
    print("DOFBOT 서버가 실행 중인지 확인하세요.")
    sys.exit(1)

print("[OK] 로봇 연결 성공\n")

# 모든 관절각을 0으로 설정
zero_joints = [90, 90, 90, 90, 90]

print(f"관절각을 모두 0으로 설정합니다: {zero_joints}")
print("로봇이 이동합니다...\n")

robot.set_joints(zero_joints)
time.sleep(3.0)  # 이동 대기

# 결과 확인
print("=" * 60)
print("이동 완료! 현재 상태 확인")
print("=" * 60)

pose = robot.get_current_pose()

print(f"\n위치 (cm):")
print(f"  x = {pose['position']['x']:.2f}")
print(f"  y = {pose['position']['y']:.2f}")
print(f"  z = {pose['position']['z']:.2f}")

print(f"\n관절 각도 (degrees):")
for i, angle in enumerate(pose['joints']):
    print(f"  Joint {i+1}: {angle:.1f}°")

print("\n" + "=" * 60)
print("테스트 완료")
print("=" * 60)

# 정리
robot.disconnect()
