from fastapi import FastAPI, WebSocket, BackgroundTasks, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import time

# sys.path hacking removed as we run from root
# from pathlib import Path
# BASE_DIR = Path(__file__).resolve().parent.parent.parent
# sys.path.append(str(BASE_DIR))

from shared.state_broadcaster import broadcaster
from brain.logic_brain import logic_brain
from expression.emotion_controller import emotion_controller
from brain.emotion_updater import llm_updater
from sensor.realsense_driver import realsense_driver
from interface.backend.pybullet_client import pybullet_client
from memory.falkordb_manager import memory_manager

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # 센서 루프 시작
    realsense_driver.start()
    
    # 분리된 감정 시스템 시작
    emotion_controller.start()  # 고속 보간 (백그라운드 스레드)
    llm_updater.start()         # 저속 목표 추론 (백그라운드 스레드)
    
    # 로봇 제어기 시작 (상주)
    from embodiment.robot_controller import robot_controller
    robot_controller.start()
    
    # 메모리 연결
    memory_manager.connect()

@app.on_event("shutdown")
async def shutdown_event():
    realsense_driver.stop()
    emotion_controller.stop()
    llm_updater.stop()
    
    from embodiment.robot_controller import robot_controller
    robot_controller.stop()

@app.get("/")
def read_root():
    return {"status": "MACH_VII_v2.0 Online"}

# WebSocket 엔드포인트: React로 업데이트 스트리밍
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # 1. 스냅샷 획득
            brain_state = broadcaster.get_snapshot()
            emotion_state = emotion_controller.get_current_emotion()
            perception_state = realsense_driver.get_state()
            
            # 2. 패킷 포장
            packet = {
                "brain": brain_state,
                "emotion": emotion_state,
                "perception": perception_state,
                "memory": {"connected": memory_manager.connected},
                "timestamp": time.time()
            }
            
            # 3. 전송
            await websocket.send_text(json.dumps(packet))
            
            # 4. 대기 (스트리밍 속도 조절)
            await asyncio.sleep(0.016)
            
            await asyncio.sleep(0.016)
            
    except WebSocketDisconnect:
        # 정상적인 연결 종료
        pass
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"WS Error: {e}")

# API 엔드포인트: 작업 명령 (Task Command)
@app.post("/api/command")
async def post_command(command: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(logic_brain.execute_task, command)
    return {"status": "accepted", "command": command}

# API 엔드포인트: 컨텍스트 업데이트 (UI Controls)
@app.post("/api/context")
async def update_context(allow_explore: bool, risk_level: str):
    logic_brain.set_context(allow_explore, risk_level)
    return {"status": "updated", "context": {"allow_explore": allow_explore, "risk_level": risk_level}}

# Video Streaming Endpoints
@app.get("/video/rgb")
def video_rgb(source: str = None):
    # Driver now handles PyBullet fetching + YOLO internally
    return StreamingResponse(realsense_driver.generate_rgb_stream(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/video/depth")
def video_depth():
    # Only RealSense supports depth stream currently in this architecture
    # PyBullet provides raw depth but we might need to visualizing it if requested
    # For now, return existing stream (which handles Mock/Real)
    return StreamingResponse(realsense_driver.generate_depth_stream(), media_type="multipart/x-mixed-replace; boundary=frame")

    return {"status": "updated", "context": {"allow_explore": allow_explore, "risk_level": risk_level}}

# Configuration Endpoint
@app.post("/api/config")
async def update_config(camera_source: str = None, robot_target: str = None, logic_mode: str = None):
    # Handle Camera Switch
    if camera_source:
        realsense_driver.set_source(camera_source)
        if camera_source == "PyBullet":
             pybullet_client.connect()
    
    # Handle Logic/Robot (Placeholder for logic brain update)
    # if logic_mode:
    #     logic_brain.set_mode(logic_mode)
    
    return {
        "status": "config_updated", 
        "config": {
            "camera": camera_source, 
            "robot": robot_target, 
            "logic": logic_mode
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
