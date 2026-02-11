# embodiment/dofbot_robot.py

import logging
import socketio
import threading
import time
from typing import Tuple, Optional
from .robot_base import RobotBase
from shared.config import GlobalConfig

class DofbotRobot(RobotBase):
    """
    [Layer 6: Embodiment] DOFBOT 실물 로봇 클라이언트 구현체입니다.
    
    DOFBOT 서버(DOFBOT_ROBOT_ARM-main/main.py)와 SocketIO를통해 통신하며,
    RobotBase 인터페이스를 준수하여 MACH_VII 아키텍처에 통합됩니다.
    
    서버는 포트 5000에서 Flask-SocketIO로 동작하며, 이 클라이언트는 다음 이벤트를 사용합니다:
    - set_pos: 목표 위치 전송 {"pos": [x, y, z]} (미터 단위)
    - set_gripper: 그리퍼 각도 전송 {"gripper": angle} (0-170도)
    - set_force: 로봇 힘 설정 {"force": value}
    - robot_state: 로봇 상태 수신 {"ee": {x, y, z}, "joints": [...]}
    """
    
    def __init__(self):
        """
        DOFBOT 서버와의 SocketIO 연결을 초기화합니다.
        """
        self.sio = socketio.Client()
        self.server_url = GlobalConfig.DOFBOT_SERVER_URL
        self.connected = False
        
        # 로봇 상태 버퍼 (서버로부터 수신)
        self.latest_state = {}
        self.state_lock = threading.Lock()
        
        # 연결 상태 관리를 위한 락
        self.connect_lock = threading.Lock()
        
        # SocketIO 이벤트 핸들러 등록
        self.sio.on('connect', self._on_connect)
        self.sio.on('disconnect', self._on_disconnect)
        self.sio.on('robot_state', self._on_robot_state)
        
        logging.info(f"[DofbotRobot] 클라이언트 초기화 완료 (서버: {self.server_url})")
        
    def connect(self, timeout=10):
        """
        DOFBOT 서버에 연결합니다.
        """
        if self.connected: return
        
        with self.connect_lock:
            if self.connected: return
            try:
                logging.info(f"[DofbotRobot] DOFBOT 서버 연결 중... ({self.server_url})")
                self.sio.connect(
                    self.server_url,
                    transports=['websocket', 'polling'],
                    wait_timeout=timeout
                )
                self.connected = True
                logging.info("[DofbotRobot] DOFBOT 서버 연결 성공")
            except Exception as e:
                logging.error(f"[DofbotRobot] DOFBOT 서버 연결 실패: {e}")
                logging.warning(f"[DofbotRobot] DOFBOT 서버가 {self.server_url}에서 실행 중인지 확인하세요.")
                self.connected = False
                
    def disconnect(self):
        """
        DOFBOT 서버 연결을 종료합니다.
        """
        if self.sio.connected:
            self.sio.disconnect()
        self.connected = False
        logging.info("[DofbotRobot] DOFBOT 서버 연결 종료")
    
    def _on_connect(self):
        """SocketIO 연결 성공 콜백"""
        self.connected = True
        logging.info("[DofbotRobot] SocketIO 연결됨")
    
    def _on_disconnect(self):
        """SocketIO 연결 끊김 콜백"""
        self.connected = False
        logging.info("[DofbotRobot] SocketIO 연결 끊김")
    
    def _on_robot_state(self, data):
        """
        로봇 상태 수신 콜백
        data = {"ee": {x, y, z}, "joints": [j1, j2, j3, j4, j5]}
        """
        with self.state_lock:
            self.latest_state = data
            
    def move_to(self, x: float, y: float, z: float, speed: float = 1.0, wait: bool = True) -> bool:
        """
        로봇을 지정된 XYZ 좌표로 이동시킵니다.
        
        Args:
            x, y, z: 목표 위치 (cm 단위)
            speed: 이동 속도 (사용하지 않음, DOFBOT 서버에서 duration으로 제어)
            wait: 이동 완료 대기 여부
            
        Returns:
            bool: 명령 전송 성공 여부
        """
        if not self.connected:
            logging.warning("[DofbotRobot] 서버에 연결되지 않음. 연결 시도...")
            self.connect()
            if not self.connected:
                logging.error("[DofbotRobot] 서버 연결 실패. 이동 명령 취소")
                return False
        
        try:
            # cm 단위를 미터 단위로 변환 (DOFBOT 서버는 미터 단위 사용)
            x_m = x / 100.0
            y_m = y / 100.0
            z_m = z / 100.0
            
            logging.info(f"[DofbotRobot] 이동 명령: ({x:.1f}, {y:.1f}, {z:.1f})cm "
                        f"→ DOFBOT: ({x_m:.3f}, {y_m:.3f}, {z_m:.3f})m")
            
            # DOFBOT 서버로 위치 명령 전송
            self.sio.emit('set_pos', {'pos': [x_m, y_m, z_m]})
            
            if wait:
                # 간단한 대기 로직 (실제로는 서버의 duration 만큼 소요)
                time.sleep(1.0)  # DOFBOT 서버의 기본 duration은 1000ms
                logging.info("[DofbotRobot] 이동 완료 (예상)")
            
            return True
            
        except Exception as e:
            logging.error(f"[DofbotRobot] 이동 중 오류 발생: {e}")
            return False
    
    def move_to_xyz(self, x: float, y: float, z: float, speed: int = 50) -> bool:
        """
        [RobotBase 인터페이스] 목표 좌표(x, y, z)로 로봇 끝단을 이동시킵니다.
        
        Args:
            x, y, z: 목표 좌표 (단위: cm)
            speed: 이동 속도 (0 ~ 100)
        Returns:
            bool: 이동 성공 여부
        """
        # 내부적으로 move_to() 메소드를 활용하여 구현
        # speed 파라미터는 DOFBOT 서버에서 duration으로 제어되므로 무시
        return self.move_to(x, y, z, wait=True)
    
    def set_joints(self, angles: list, speed: int = 50) -> bool:
        """
        [RobotBase 인터페이스] 5개 관절의 각도를 직접 제어합니다.
        
        Args:
            angles: 5개 관절의 목표 각도 리스트 (단위: 도)
            speed: 이동 속도 (0 ~ 100)
        Returns:
            bool: 명령 전송 성공 여부
        """
        if not self.connected:
            logging.warning("[DofbotRobot] 서버에 연결되지 않음")
            return False
        
        if len(angles) != 5:
            logging.error(f"[DofbotRobot] 잘못된 관절 개수: {len(angles)} (예상: 5)")
            return False
        
        try:
            logging.info(f"[DofbotRobot] 관절 제어: {angles}")
            # DOFBOT 서버로 관절 각도 명령 전송
            # 서버에 'set_joints' 이벤트가 구현되어 있다고 가정
            self.sio.emit('set_joints', {'joints': angles})
            return True
        except Exception as e:
            logging.error(f"[DofbotRobot] 관절 제어 중 오류 발생: {e}")
            return False
    
    def set_gripper(self, open_percent: float) -> bool:
        """
        그리퍼를 제어합니다.
        
        Args:
            open_percent: 개폐 정도 (0.0 = 완전 닫힘, 100.0 = 완전 열림)
            
        Returns:
            bool: 명령 전송 성공 여부
        """
        if not self.connected:
            logging.warning("[DofbotRobot] 서버에 연결되지 않음")
            return False
            
        try:
            # 퍼센트를 각도로 변환 (0-100% → 10-170도)
            # DOFBOT 서보 그리퍼: 10도=닫힘, 170도=열림
            angle = 10 + (open_percent / 100.0) * 160
            angle = max(10, min(170, int(angle)))  # 안전 범위 제한
            
            logging.info(f"[DofbotRobot] 그리퍼 동작: {open_percent:.1f}% → {angle}도")
            
            # DOFBOT 서버로 그리퍼 명령 전송
            self.sio.emit('set_gripper', {'gripper': angle})
            return True
            
        except Exception as e:
            logging.error(f"[DofbotRobot] 그리퍼 제어 중 오류 발생: {e}")
            return False
    
    def move_gripper(self, open_percent: float) -> bool:
        """
        [RobotBase 인터페이스] 그리퍼의 개폐를 제어합니다.
        0%는 0m(닫힘), 100%는 0.03m(3cm 열림)에 매핑됩니다.
        
        Args:
            open_percent: 그리퍼 개방 정도 (0 ~ 100)
        Returns:
            bool: 명령 전송 성공 여부
        """
        # 내부적으로 set_gripper() 메소드를 활용하여 구현
        return self.set_gripper(open_percent)
    
    def set_force(self, force: float) -> bool:
        """
        로봇 구동 힘을 설정합니다.
        
        Args:
            force: 힘 설정 값 (0.0 ~ 1.0)
            
        Returns:
            bool: 명령 전송 성공 여부
        """
        if not self.connected:
            logging.warning("[DofbotRobot] 서버에 연결되지 않음")
            return False
            
        try:
            # 0.0-1.0 범위를 0-100 범위로 변환
            force_value = force * 100.0
            force_value = max(0, min(100, int(force_value)))
            
            logging.info(f"[DofbotRobot] 힘 설정: {force:.2f} → {force_value}")
            self.sio.emit('set_force', {'force': force_value})
            return True
            
        except Exception as e:
            logging.error(f"[DofbotRobot] 힘 설정 중 오류 발생: {e}")
            return False
    
    def get_current_pose(self) -> dict:
        """
        [RobotBase 인터페이스] 로봇의 현재 좌표, 관절 각도, 그리퍼 상태를 반환합니다.
        
        Returns:
            dict: {"position": {"x": float, "y": float, "z": float}, 
                   "joints": [float, ...], 
                   "gripper": float, 
                   "is_moving": bool}
        """
        with self.state_lock:
            if not self.latest_state:
                # 상태가 없으면 기본값 반환
                return {
                    "position": {"x": 0.0, "y": 0.0, "z": 0.0},
                    "joints": [0.0] * 5,
                    "gripper": 0.0,
                    "is_moving": False
                }
            
            # DOFBOT 서버로부터 받은 상태를 RobotBase 형식으로 변환
            ee_state = self.latest_state.get('ee', {})
            joints_state = self.latest_state.get('joints', [0.0] * 5)
            
            # 미터를 cm로 변환
            x_cm = ee_state.get('x', 0) * 100.0
            y_cm = ee_state.get('y', 0) * 100.0
            z_cm = ee_state.get('z', 0) * 100.0
            
            return {
                "position": {"x": x_cm, "y": y_cm, "z": z_cm},
                "joints": joints_state,
                "gripper": 0.0,  # DOFBOT 서버에서 그리퍼 상태를 전송하면 업데이트 필요
                "is_moving": False  # 실제 이동 상태는 서버에서 받아야 함
            }
    
    def get_current_position(self) -> Optional[Tuple[float, float, float]]:
        """
        현재 로봇 엔드 이펙터의 위치를 cm 단위 튜플로 반환합니다.
        (레거시 호환성을 위한 헬퍼 메소드)
        
        Returns:
            (x, y, z) 튜플 (cm 단위), 또는 상태를 가져올 수 없으면 None
        """
        pose = self.get_current_pose()
        if pose and "position" in pose:
            pos = pose["position"]
            return (pos["x"], pos["y"], pos["z"])
        return None
    
    def emergency_stop(self):
        """
        [RobotBase 인터페이스] 긴급 정지를 수행합니다.
        현재 위치를 목표 위치로 전송하여 이동을 중단시킵니다.
        """
        logging.warning("[DofbotRobot] 긴급 정지!")
        pos_tuple = self.get_current_position()
        if pos_tuple:
            x, y, z = pos_tuple
            self.move_to(x, y, z, wait=False)
