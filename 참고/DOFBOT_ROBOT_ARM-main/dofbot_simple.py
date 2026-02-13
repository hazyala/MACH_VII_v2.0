import time
import math
import numpy as np
import os

#Dofbot 하드웨어 제어 라이브러리
from Arm_Lib import Arm_Device

#URDF로 정의된 로봇 구조를 기반으로 FK, IK를 수행한다
#XYZ 좌표 제어 핵심 엔진
import ikpy.chain


#실제 하드웨어 제어와 FK,IK 계산 엔진을 하나로 묶어서 외부 코드에서 XYZ의 좌표 제어 명령으로 사용
class DofbotSimple:
    def __init__(self, urdf_file_name):

        # Dofbot 하드웨어 제어 객체 생성
        self.Arm = Arm_Device()
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        urdf_path = os.path.join(current_dir, urdf_file_name)
        
        # URDF 기반으로 IKPy 체인 생성
        self.chain = ikpy.chain.Chain.from_urdf_file(
            urdf_path,

            #IK 계산에 사용할 관절 선택 마스크
            #false: 고정(그리퍼 등 관절이 움직이지 )
            active_links_mask=[False, True, True, True, True, True, False]
        )
        
        self.gripper_angle = None
        
        #실제 하드웨어 상태와 IK모델을 동기화
        self._sync_hardware_state()
        print(">>> Standard IK Controller Loaded")

    #실제 서보모터 각도를 읽어 IKPy 체인 관절 상태와 일치 시키는 함수
    def _sync_hardware_state(self):

        #IKpy 체인에 필요한 전체 링크 7개의 배열 생성
        real_joints = [0.0] * 7
        
        #실제 서보 모터 수는 6개이므로 7개를 사용하지 않는다 
        for i in range(1, 6):
            angle = self.Arm.Arm_serial_servo_read(i)

            #서보모터 관절을 읽지 못하면 중간 각도(90도)로 가정한다
            if angle is None:
                angle = 90

            ##IKPy는 회전 중심이 0인 라디안 단위를 사용하므로
            #서보 각도 범위(0~180)를 IK 각도 범위(-90 ~ 90)범위로 변환
            #IK 계산 시준과 실제 로봇 기준이 다르므로 조정이 필요하다
            radian = math.radians(angle - 90)
            real_joints[i] = radian

        #그리퍼 상태 읽기
        gripper_val = self.Arm.Arm_serial_servo_read(6)
        if gripper_val is not None:
            self.gripper_angle = int(gripper_val)

        #현재 관절 각도를 이용해 FK로 TCP 위치를 계산
        transformation_matrix = self.chain.forward_kinematics(real_joints)

        #위치 정보 반환
        current_pos = transformation_matrix[:3, 3]

        self.last_joints = real_joints
        self.last_pos = [current_pos[0], current_pos[1], current_pos[2]]
        
        print(f"Sync Position (Real): X={self.last_pos[0]:.3f}, Y={self.last_pos[1]:.3f}, Z={self.last_pos[2]:.3f}")

    #def go_home(self):
        #self.Arm.Arm_serial_servo_write6(90, 90, 90, 90, 90, 5, 1000)
        #time.sleep(1.5)
        #self._sync_hardware_state()

    #그리퍼 조작 함수
    def set_gripper(self, angle, duration_ms=1500):

        #물리적 한계 방지
        #10이하면 10으로, 170이상이면 170으로 반환
        angle = int(max(10, min(170, angle)))
        if self.gripper_angle == angle:
           return
        
        self.gripper_angle = angle
        self.Arm.Arm_serial_servo_write(6, angle, int(duration_ms))


    #로봇 엔드 이펙터를 지정한 XYZ 좌표로 이동시킨다
    #IKPy로 목표 좌표로 이동하기 위한 관절 각도를 계산
    #자동으로 실제 서보모터에 이동명령을 내리기 때문에 각 관절 각도를 직접 계산 할 필요가 없다
    def move_to_xyz(self, x, y, z, duration_ms=1500):
        target_position = [x, y, z]
        
        ik_angles = self.chain.inverse_kinematics(
            target_position, 
            orientation_mode=None, 
            # initial_position=self.last_joints
        )

        self.last_joints = ik_angles
        self.last_pos = [x, y, z]

        print(f"Moving to: {x:.2f}, {y:.2f}, {z:.2f}")
        self._send_servos(ik_angles, duration_ms)
    
    #관절 각도를 직접 설정하는 함수 (degrees 단위)
    def set_joints_direct(self, joints_deg, duration_ms=1500):
        """
        관절 각도를 직접 설정합니다 (IK 우회).
        joints_deg: [j1, j2, j3, j4, j5] 각도 리스트 (degrees)
        """
        if len(joints_deg) != 5:
            print(f"Error: Expected 5 joint angles, got {len(joints_deg)}")
            return
        
        # Degrees를 서보 각도(0~180)로 변환
        # 클라이언트에서 보낸 각도가 -90~90 범위라고 가정하면 +90 오프셋
        safe = [int(max(0, min(180, j + 90))) for j in joints_deg]
        
        print(f"Setting Joints Directly: {joints_deg} -> Servo:{safe}")
        
        # 서보 모터에 직접 명령
        self.Arm.Arm_serial_servo_write6(
            safe[0], safe[1], safe[2],
            safe[3], safe[4], self.gripper_angle if self.gripper_angle is not None else 90,
            int(duration_ms)
        )
        
        # FK로 예상 위치 계산 (상태 동기화)
        ik_joints = [0] + [math.radians(j) for j in joints_deg] + [0]
        self.last_joints = ik_joints
        transformation_matrix = self.chain.forward_kinematics(ik_joints)
        current_pos = transformation_matrix[:3, 3]
        self.last_pos = [current_pos[0], current_pos[1], current_pos[2]]

    #IKPy에서 계산한 관절 각도를 서보모터 각도로 변환
    def _send_servos(self, ik_angles, duration_ms):

        #라디안 -> 각도 변환 보정 오프셋
        s1 = 90 + math.degrees(ik_angles[1])
        s2 = 90 + math.degrees(ik_angles[2])
        s3 = 90 + math.degrees(ik_angles[3])
        s4 = 90 + math.degrees(ik_angles[4])
        s5 = 90

        safe = [int(max(0, min(180, a))) for a in [s1, s2, s3, s4, s5]]
        
        #val = self.Arm.Arm_serial_servo_read(6)
        #s6 = val if val is not None else (self.gripper_angle or 90)
        
        #6축 서보 모터 동시 제어(그리퍼 제외)
        self.Arm.Arm_serial_servo_write6(
            safe[0], safe[1], safe[2],
            safe[3], safe[4], self.gripper_angle if self.gripper_angle is not None else 90,
            int(duration_ms)
        )
