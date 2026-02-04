# verify_gripper_cam.py
import time
import base64
from state.system_state import system_state
from sensor.perception.perception_manager import perception_manager
from shared.config import GlobalConfig

def verify():
    print("Verifying Gripper Camera population...")
    GlobalConfig.SIM_MODE = True
    
    # Start PerceptionManager in a way that doesn't block
    perception_manager.start()
    
    time.sleep(2) # Wait for some loops
    
    ee_frame = system_state.last_ee_frame_base64
    main_frame = system_state.last_frame_base64
    
    if main_frame:
        print(f"✅ Main frame captured (size: {len(main_frame)})")
    else:
        print("❌ Main frame NOT captured")
        
    if ee_frame:
        print(f"✅ Gripper frame captured (size: {len(ee_frame)})")
    else:
        print("❌ Gripper frame NOT captured")
        
    perception_manager.stop()

if __name__ == "__main__":
    verify()
