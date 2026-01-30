# brain/tools/grasp_object.py

from langchain_core.tools import tool
from sensor.vision_bridge import VisionBridge
from strategy.grasp_planner import grasp_planner
from strategy.visual_servoing import visual_servoing
from embodiment.robot_controller import robot_controller
import logging

@tool
def grasp_object(object_name: str = "물체") -> str:
    """
    지정된 물체를 감지하고 정밀하게 잡는 도구입니다.
    
    IMPORTANT: object_name은 YOLO가 감지하는 영어 클래스명을 사용해야 합니다.
    예: "kite" (연), "cup" (컵), "bottle" (병), "teddy" (곰인형), "soccerball" (축구공)
    
    색상이 지정된 경우: "yellow kite", "red cup" 형식으로 전달하세요.
    
    GPD(Grasp Pose Detection)와 비주얼 서보잉을 사용하여:
    1. 물체 감지 (YOLO + 칼만 필터)
    2. 색상/속성이 지정된 경우 VLM으로 정확한 객체 식별
    3. 그립 자세 계산 (GPD)
    4. 비주얼 서보잉으로 정밀 접근
    5. 그리퍼로 물체 잡기
    
    Args:
        object_name: 잡을 물체의 영어 이름 (예: "kite", "yellow kite", "red cup")
                    또는 "물체" (가장 가까운 물체 자동 선택)
    """
    try:
        # 1. 비전 시스템으로 물체 탐지
        logging.info(f"[GraspTool] '{object_name}' 탐지 시작...")
        vision = VisionBridge()
        detections = vision.get_refined_detections()
        
        if not detections:
            return "[실패] 시야에서 물체를 발견하지 못했습니다."
        
        # 2. 색상이나 특정 속성이 포함된 경우, VLM으로 정확한 객체 식별
        color_keywords = ["red", "yellow", "blue", "green", "white", "black", "purple", "pink", 
                         "orange", "빨간", "빨강", "노란", "노랑", "파란", "파랑", "초록", 
                         "흰", "검은", "검정", "보라", "분홍"]
        has_color_attr = any(keyword in object_name.lower() for keyword in color_keywords)
        
        target = None
        
        if has_color_attr and len(detections) > 1:
            # VLM을 사용하여 정확한 물체 식별
            logging.info(f"[GraspTool] 색상/속성 감지 - VLM으로 '{object_name}' 식별 중...")
            
            from .vision_analyze import vision_analyze
            
            # VLM에게 물체 위치 질문
            query = f"화면에 보이는 물체들 중에서 '{object_name}'의 위치를 알려주세요. " \
                   f"화면의 왼쪽, 중앙, 오른쪽 중 어디에 있나요? 그리고 위, 중간, 아래 중 어디인가요?"
            
            vlm_result = vision_analyze.invoke({"query": query})
            logging.info(f"[GraspTool] VLM 분석 결과: {vlm_result}")
            
            # VLM 응답에서 위치 힌트 추출 (간단한 휴리스틱)
            vlm_lower = vlm_result.lower()
            
            # 위치 기반 필터링
            if "왼쪽" in vlm_lower or "left" in vlm_lower:
                # X 좌표가 작은 것 선택
                target = min(detections, key=lambda d: d['position']['x'])
            elif "오른쪽" in vlm_lower or "right" in vlm_lower:
                # X 좌표가 큰 것 선택
                target = max(detections, key=lambda d: d['position']['x'])
            elif "중앙" in vlm_lower or "center" in vlm_lower or "가운데" in vlm_lower:
                # X 좌표가 0에 가까운 것 선택
                target = min(detections, key=lambda d: abs(d['position']['x']))
            else:
                # VLM이 명확한 위치를 제공하지 못한 경우, 가장 가까운 물체 선택
                target = min(detections, key=lambda d: 
                            (d['position']['x']**2 + d['position']['y']**2 + d['position']['z']**2)**0.5)
                logging.warning(f"[GraspTool] VLM 위치 불명확 - 가장 가까운 물체 선택")
        
        else:
            # 3. 일반적인 객체 선택 (색상 없는 경우)
            if object_name == "물체":
                # 가장 가까운 물체 선택
                target = min(detections, key=lambda d: 
                            (d['position']['x']**2 + d['position']['y']**2 + d['position']['z']**2)**0.5)
            else:
                # 이름으로 검색 (대소문자 무시, 부분 매칭)
                for det in detections:
                    det_name = det['name'].lower()
                    search_name = object_name.lower()
                    
                    # "yellow kite" → "kite" 추출하여 매칭
                    if search_name in det_name or det_name in search_name:
                        target = det
                        break
        
        if not target:
            return f"[실패] '{object_name}'을(를) 찾을 수 없습니다. 감지된 물체: {[d['name'] for d in detections]}"
        
        obj_name = target['name']
        obj_pos = target['position']
        logging.info(f"[GraspTool] 목표 물체: {obj_name} at ({obj_pos['x']:.1f}, {obj_pos['y']:.1f}, {obj_pos['z']:.1f})cm")
        
        # 3. GPD로 그립 자세 계산
        grasp_pose = grasp_planner.compute_grasp_pose(obj_name, obj_pos)
        
        # 4. 그리퍼 열기
        robot_controller.robot_driver.move_gripper(grasp_pose['gripper_width'])
        logging.info(f"[GraspTool] 그리퍼 개방: {grasp_pose['gripper_width']}%")
        
        # 5. 비주얼 서보잉으로 접근 위치로 이동
        pre_grasp = grasp_pose['pre_grasp']
        logging.info(f"[GraspTool] 접근 위치로 이동: ({pre_grasp['x']:.1f}, {pre_grasp['y']:.1f}, {pre_grasp['z']:.1f})cm")
        
        def get_ee_pos():
            return robot_controller.robot_driver.get_current_pose()
        
        def move_robot(pos, speed):
            return robot_controller.robot_driver.move_to_xyz(pos['x'], pos['y'], pos['z'], speed)
        
        # 접근 위치까지 서보잉 (기본 max_iterations=300 사용)
        success = visual_servoing.servoing_loop(
            target_position=pre_grasp,
            get_ee_position=get_ee_pos,
            move_robot=move_robot
        )
        
        if not success:
            return f"[실패] {obj_name}에 접근하지 못했습니다."
        
        # 6. 잡기 위치로 정밀 하강
        grasp_pos = grasp_pose['grasp']
        logging.info(f"[GraspTool] 잡기 위치로 하강: ({grasp_pos['x']:.1f}, {grasp_pos['y']:.1f}, {grasp_pos['z']:.1f})cm")
        
        success = visual_servoing.servoing_loop(
            target_position=grasp_pos,
            get_ee_position=get_ee_pos,
            move_robot=move_robot
        )
        
        if not success:
            return f"[실패] {obj_name}을(를) 정확히 잡지 못했습니다."
        
        # 7. 그리퍼 닫기
        robot_controller.robot_driver.move_gripper(0)
        logging.info("[GraspTool] 그리퍼 닫기 - 물체 파지 완료")
        
        # 8. 약간 들어올리기
        current_pos = robot_controller.robot_driver.get_current_pose()
        robot_controller.robot_driver.move_to_xyz(current_pos['x'], current_pos['y'], current_pos['z'] + 10)
        
        return f"[성공] {obj_name}을(를) 성공적으로 잡았습니다!"
        
    except Exception as e:
        logging.error(f"[GraspTool] 오류 발생: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return f"[오류] 물체 잡기 실패: {str(e)}"
