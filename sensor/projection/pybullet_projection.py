import logging
import numpy as np
import math

# PyBullet 라이브러리 가용성 체크
PYBULLET_AVAILABLE = False
try:
    import pybullet as p
    PYBULLET_AVAILABLE = True
except ImportError:
    PYBULLET_AVAILABLE = False
    logging.warning("[PyBulletProjection] pybullet 모듈을 찾을 수 없습니다. 시뮬레이션 투영 기능을 사용할 수 없습니다.")

# PyBullet 카메라 설정 (pybullet_sim.py와 일치해야 함)
CAMERA_CONFIG = {
    "width": 600,
    "height": 480,
    "fov": 60,  # degrees (수직 FOV)
    "near": 0.01,
    "far": 10.0,
    "camera_eye": [0.5, 0.0, 0.5],     # 카메라 위치 (m)
    "camera_target": [0.0, 0.0, 0.0],  # 카메라 타겟 (m)
    "camera_up": [0.0, 0.0, 1.0]       # 상단 벡터
}

def _get_camera_parameters():
    """
    PyBullet API를 통해 View/Projection Matrix(뷰/프로젝션 행렬: 3D 공간을 2D 화면으로 투영하기 위한 수학적 변환표)를 계산하고
    Intrinsic(내인자: 렌즈 속성) 및 Extrinsic(외인자: 카메라 위치/각도) 행렬을 추출합니다.
    """
    # PyBullet이 없는 경우 더미 데이터 반환 (테스트 및 비-시뮬레이션 환경 지원)
    if not PYBULLET_AVAILABLE:
        logging.warning("[PyBulletProjection] PyBullet 미설치로 인해 더미 카메라 파라미터를 사용합니다.")
        return 600.0, 600.0, 300.0, 240.0, np.eye(4)

    width = CAMERA_CONFIG["width"]
    height = CAMERA_CONFIG["height"]
    
    # 1. View Matrix(뷰 행렬: 월드 좌표를 카메라 중심 좌표로 변환) 계산 
    # (OpenGL 포맷: 4x4 리스트, Column-major: 열 우선 정렬 방식)
    view_matrix_list = p.computeViewMatrix(
        cameraEyePosition=CAMERA_CONFIG["camera_eye"],
        cameraTargetPosition=CAMERA_CONFIG["camera_target"],
        cameraUpVector=CAMERA_CONFIG["camera_up"]
    )
    # Row-major(행 우선 정렬 방식) numpy 배열로 변환
    view_matrix = np.array(view_matrix_list).reshape(4, 4, order='F')
    
    # Camera -> World (Inverse View Matrix: 카메라 좌표를 다시 월드 좌표로 되돌리는 역행렬)
    # CamToWorld = [Right  Up  -Forward  Eye]
    #              [  0    0       0      1 ]
    cam_to_world = np.linalg.inv(view_matrix)
    
    # 2. Projection Matrix(투영 행렬: 카메라 좌표를 화면의 2D 좌표로 변환) 계산
    # Camera -> NDC(기기 독립적인 표준 좌표계) 변환 행렬
    aspect = width / height
    proj_matrix_list = p.computeProjectionMatrixFOV(
        fov=CAMERA_CONFIG["fov"],
        aspect=aspect,
        nearVal=CAMERA_CONFIG["near"],
        farVal=CAMERA_CONFIG["far"]
    )
    proj_matrix = np.array(proj_matrix_list).reshape(4, 4, order='F')
    
    # 3. Intrinsic(내인자: 렌즈 고유 파라미터) 추출
    # P[0,0] = 2*fx/W  => fx = P[0,0] * W / 2
    # P[1,1] = 2*fy/H  => fy = P[1,1] * H / 2
    
    # 주의: PyBullet(OpenGL) Projection Matrix는 Screen Space가 아닌 NDC(-1~1)로 보냅니다.
    # fx, fy는 NDC 기준 스케일입니다. 픽셀 단위 fx, fy로 변환합니다.
    
    # P[0,0] = 1 / (aspect * tan(fov/2))
    # Pixel FX = W / (2 * tan(fov/2 * aspect?? No)) = W/2 * P[0,0]
    fx = proj_matrix[0, 0] * width / 2.0
    fy = proj_matrix[1, 1] * height / 2.0
    
    cx = width / 2.0
    cy = height / 2.0
    
    return fx, fy, cx, cy, cam_to_world

# 파라미터 초기화
FX, FY, CX, CY, CAM_TO_WORLD_MAT = _get_camera_parameters()

logging.info(f"[PyBulletProjection] 재계산된 파라미터: fx={FX:.2f}, fy={FY:.2f}, cx={CX:.2f}, cy={CY:.2f}")
logging.info(f"[PyBulletProjection] Cam->World:\n{CAM_TO_WORLD_MAT}")


def pixel_to_3d(pixel_x: int, pixel_y: int, depth_m: float) -> tuple:
    """
    PyBullet 픽셀 좌표를 월드 3D 좌표(cm)로 변환합니다.
    API와 동일한 매트릭스를 사용하여 오차를 제거했습니다.
    """
    if not PYBULLET_AVAILABLE:
        logging.error("[PyBulletProjection] pybullet 모듈이 없어 좌표 변환을 수행할 수 없습니다.")
        return 0.0, 0.0, 0.0
    
    # 1. 픽셀 → 카메라 좌표계 (View Space)
    # OpenGL 카메라 좌표계: X(Right), Y(Up), Z(Backward, 즉 -Forward)
    # 하지만 PyBullet의 View Matrix는 LookAt 방식이므로
    # View Space에서 물체는 -Z 방향에 있습니다. (Camera looks down -Z)
    
    # Pinhole Back-projection
    # x_cam = (u - cx) * depth / fx
    # y_cam = -(v - cy) * depth / fy  (이미지 Y는 아래로 증가, GL Y는 위로 증가 -> 반전)
    # z_cam = -depth (카메라가 보는 방향이 -Z)
    
    x_view = (pixel_x - CX) * depth_m / FX
    y_view = -(pixel_y - CY) * depth_m / FY
    z_view = -depth_m
    
    # 동차 좌표 (Homogeneous coordinates)
    view_pos = np.array([x_view, y_view, z_view, 1.0])
    
    # 2. 카메라 좌표계 → 월드 좌표계
    world_pos = CAM_TO_WORLD_MAT @ view_pos
    
    # 3. m → cm 변환
    x_cm = world_pos[0] * 100.0
    y_cm = world_pos[1] * 100.0
    z_cm = world_pos[2] * 100.0
    
    logging.info(
        f"[PyBulletProjection] "
        f"픽셀=({pixel_x}, {pixel_y}), depth={depth_m:.4f}m → "
        f"View=({x_view:.3f}, {y_view:.3f}, {z_view:.3f}) → "
        f"월드=({x_cm:.2f}, {y_cm:.2f}, {z_cm:.2f})cm"
    )
    
    return x_cm, y_cm, z_cm

def pixel_to_view_space(pixel_x: int, pixel_y: int, depth_m: float) -> tuple:
    """
    [Helper] 픽셀 좌표를 카메라 기준 3D 좌표(View Space, cm 단위)로 변환합니다.
    월드 변환 전 단계의 순수 로컬 좌표가 필요할 때 사용합니다 (예: 그리퍼 카메라).
    """
    if not PYBULLET_AVAILABLE: return 0.0, 0.0, 0.0

    # Pinhole Back-projection
    x_view = (pixel_x - CX) * depth_m / FX
    y_view = -(pixel_y - CY) * depth_m / FY
    z_view = -depth_m # PyBullet View Space는 -Z 방향
    
    # m -> cm
    return x_view * 100.0, y_view * 100.0, z_view * 100.0


def calculate_planar_depth(world_x_cm, world_y_cm, world_z_cm):
    """
    월드 좌표(cm)에 해당하는 점의 카메라 기준 Planar Depth(평면 깊이: 카메라 정면에서 수직으로 잰 거리)를 계산합니다.
    (Oracle Depth: 물리 엔진이 알려주는 오차 없는 완벽한 정답 거리를 가정할 때 사용)
    """
    # 1. cm -> m 변환
    world_pos_m = np.array([world_x_cm/100.0, world_y_cm/100.0, world_z_cm/100.0, 1.0])
    
    # 2. World -> Camera (View Matrix: 뷰 행렬) 변환
    # CAM_TO_WORLD_MAT의 역행렬이 View Matrix입니다.
    view_matrix = np.linalg.inv(CAM_TO_WORLD_MAT)
    
    view_pos = view_matrix @ world_pos_m
    
    # 3. View Space에서 카메라는 -Z 방향을 바라봅니다.
    # 따라서 Planar Depth는 -z_view 입니다.
    return -view_pos[2]

    
    return -view_pos[2]

# [Fix] Shared Memory Connection for Ground Truth Data
# Server가 회전값(Orientation)을 보내주지 않으므로,
# 로컬에서 물리 엔진 메모리에 직접 접근하여 로봇의 실제 회전값을 읽어옵니다.
# 굳이 서버 반환 요청을 안하는 이유는, 리얼센스는 SDK에서 회전값 등 모든 정보를 가져올 수 있기 때문.
_SHARED_UID = None
_ROBOT_ID = None
_EE_INDEX = None

def _get_real_ee_state():
    """
    [Direct Memory Access]
    PyBullet Shared Memory에 접속하여 실시간 True EE Pose(Pos, Orn)를 가져옵니다.
    """
    global _SHARED_UID, _ROBOT_ID, _EE_INDEX
    
    if not PYBULLET_AVAILABLE: return None, None
    
    try:
        # 1. Connection Check & Init
        if _SHARED_UID is None:
            # 먼저 연결 시도 (기존 연결 확인)
            if p.isConnected():
                _SHARED_UID = p.getConnectionInfo()['connectionMethod']
            else:
                try:
                    _SHARED_UID = p.connect(p.SHARED_MEMORY)
                except:
                    return None, None
        
        # 2. Robot ID Finding (First time)
        if _ROBOT_ID is None and p.isConnected():
            num_bodies = p.getNumBodies()
            # 간단히 첫 번째 바디 또는 'dofbot' 검색
            if num_bodies > 0:
                _ROBOT_ID = 0 # DefaultAssumption
                # EE Index Finding
                num_joints = p.getNumJoints(_ROBOT_ID)
                for i in range(num_joints):
                     info = p.getJointInfo(_ROBOT_ID, i)
                     if b'ee' in info[1] or b'tip' in info[1] or b'end_effector' in info[12]:
                         _EE_INDEX = i
                         break
                if _EE_INDEX is None: _EE_INDEX = num_joints - 1
                
        # 3. Get State
        if _ROBOT_ID is not None and _EE_INDEX is not None:
             state = p.getLinkState(_ROBOT_ID, _EE_INDEX, computeForwardKinematics=True)
             return state[4], state[5] # Pos(m), Orn(Quaternion)
             
    except Exception as e:
        logging.error(f"[PyBulletProjection] Shared Memory Access Fail: {e}")
        
    return None, None

def project_gripper_camera_to_world(point_view: list, ee_pos: list, ee_orn: list) -> list:
    """
    [Dynamic Kinematics] 그리퍼 카메라 뷰 좌표(View Space)를 월드 좌표(World Space)로 정확히 변환합니다.
    """
    if not PYBULLET_AVAILABLE: return point_view
    
    # [Bugfix] Server에서 Identity Orientation([0,0,0,1])만 보내는 경우
    # Shared Memory에서 실제 Orientation을 조회하여 덮어씁니다.
    # 단, 위치(ee_pos)는 싱크를 위해 Server 패킷값을 우선하되, Orn은 GT를 사용.
    
    use_gt = False
    # Identity Check (Epsilon)
    if abs(ee_orn[0]) < 1e-4 and abs(ee_orn[1]) < 1e-4 and abs(ee_orn[2]) < 1e-4 and abs(ee_orn[3]-1) < 1e-4:
        use_gt = True
    elif ee_orn == [0,0,0,0]: # Invalid
        use_gt = True
        
    if use_gt:
        real_pos, real_orn = _get_real_ee_state()
        if real_orn is not None:
            ee_orn = real_orn
            # logging.debug(f"[PyBulletProjection] GT Orientation Patch: {ee_orn}")
            
    # 1. View Space -> EE Local Space 변환
    # Basis Change: (x, y, z) -> (-y, -x, -z)
    p_local = np.array([-point_view[1], -point_view[0], -point_view[2]]) # cm 단위
    
    # 2. Rotate Local -> World
    # Quaternion -> Rotation Matrix
    rot_matrix = np.array(p.getMatrixFromQuaternion(ee_orn)).reshape(3, 3)
    
    # 3. Apply Rotation & Translation
    # P_world = R * P_local + T
    # T는 cm 단위로 변환 필요 (ee_pos는 m)
    t_world = np.array(ee_pos) * 100.0
    
    p_world = rot_matrix @ p_local + t_world
    
    return p_world.tolist()
