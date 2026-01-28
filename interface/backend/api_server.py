from fastapi import FastAPI, WebSocket, BackgroundTasks, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import time

from shared.pipeline import pipeline
from shared.state_broadcaster import broadcaster
from brain.logic_brain import logic_brain
from expression.emotion_controller import emotion_controller
from brain.emotion_updater import llm_updater
from sensor.realsense_driver import realsense_driver
from interface.backend.pybullet_client import pybullet_client
from memory.falkordb_manager import memory_manager
from strategy.strategy_manager import strategy_manager

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
    # 1. 하위 계층 드라이버 및 루프 시작
    realsense_driver.start()
    emotion_controller.start()
    llm_updater.start()
    
    from embodiment.robot_controller import robot_controller
    robot_controller.start()
    
    # 2. [핵심] 파이프라인 컴포넌트 등록
    # 7단계 레이어 아키텍처의 인스턴스를 파이프라인에 연결합니다.
    pipeline.register_component("emotion_controller", emotion_controller)
    pipeline.register_component("robot_controller", robot_controller)
    pipeline.register_component("realsense_driver", realsense_driver)
    
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
    return {"status": "MACH_VII_v2.0 Online (Pipeline Active)"}

# WebSocket 엔드포인트: 파이프라인 기반 통합 스냅샷 스트리밍
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # 파이프라인을 통해 정합성이 보장된 7단계 레이어의 상태 획득 (단방향 흐름 반영)
            packet = pipeline.get_system_snapshot()
            
            await websocket.send_text(json.dumps(packet))
            await asyncio.sleep(0.016) # ~60fps
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"WS Error: {e}")

# API 엔드포인트: 작업 명령 (Task Command)
@app.post("/api/command")
async def post_command(command: str, background_tasks: BackgroundTasks):
    # 브레인에게 작업을 위임합니다.
    background_tasks.add_task(logic_brain.execute_task, command)
    return {"status": "accepted", "command": command}

# API 엔드포인트: 전략 컨텍스트 업데이트 (Layer 4)
@app.post("/api/context")
async def update_context(allow_explore: bool, risk_level: str):
    # 브레인이 아닌 전략 매니저에게 직접 명령을 하달합니다.
    strategy_manager.set_context(allow_explore=allow_explore, risk_level=risk_level)
    return {"status": "updated", "context": {"allow_explore": allow_explore, "risk_level": risk_level}}

# Video Streaming Endpoints
@app.get("/video/rgb")
def video_rgb(source: str = None):
    return StreamingResponse(realsense_driver.generate_rgb_stream(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/video/depth")
def video_depth():
    return StreamingResponse(realsense_driver.generate_depth_stream(), media_type="multipart/x-mixed-replace; boundary=frame")

# Configuration Endpoint
@app.post("/api/config")
async def update_config(camera_source: str = None, robot_target: str = None, logic_mode: str = None):
    if camera_source:
        realsense_driver.set_source(camera_source)
        if camera_source == "PyBullet":
             pybullet_client.connect()
    
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
