import threading
import time
import math
import shared
from dofbot_simple import DofbotSimple

def run_robot_loop():
    print(">>> Robot Control Thread Started")
    
    try:
        bot = DofbotSimple("dofbot.urdf")
        
        print(">>> Syncing Initial State to Network...")
        with shared.state_lock:
            shared.robot_state["x"] = bot.last_pos[0]
            shared.robot_state["y"] = bot.last_pos[1]
            shared.robot_state["z"] = bot.last_pos[2]
            
            if hasattr(bot, 'last_joints'):
                degrees = [math.degrees(rad) for rad in bot.last_joints]
                shared.joints_degrees = degrees[1:6]
        
    except Exception as e:
        print(f"!!! Robot Init Failed: {e}")
        return

    while True:
        target_pos = None
        gripper_cmd = None
        joint_cmd = None
        
        with shared.cmd_lock:
            if shared.command["target_pos"] is not None:
                target_pos = shared.command["target_pos"]
                shared.command["target_pos"] = None
            
            if shared.command["gripper_cmd"] is not None:
                gripper_cmd = shared.command["gripper_cmd"]
                shared.command["gripper_cmd"] = None
            
            if shared.command["joint_cmd"] is not None:
                joint_cmd = shared.command["joint_cmd"]
                shared.command["joint_cmd"] = None

        if gripper_cmd is not None:
            try:
                angle = int(float(gripper_cmd))
                print(f"Gripper Command: {angle}")
                bot.set_gripper(angle)
                
            except Exception as e:
                print(f"Gripper Error: {e}")
        
        if joint_cmd is not None:
            try:
                if isinstance(joint_cmd, list) and len(joint_cmd) == 5:
                    joints = [float(j) for j in joint_cmd]
                    print(f"Joint Command: {joints}")
                    bot.set_joints_direct(joints, duration_ms=1000)
                else:
                    print(f"Invalid Joint Command: {joint_cmd}")
            except Exception as e:
                print(f"Joint Error: {e}")

        if target_pos is not None:
            try:
                x, y, z = 0.0, 0.0, 0.0
                
                if isinstance(target_pos, list) or isinstance(target_pos, tuple):
                    x = float(target_pos[0])
                    y = float(target_pos[1])
                    z = float(target_pos[2])
                elif isinstance(target_pos, dict):
                    x = float(target_pos['x'])
                    y = float(target_pos['y'])
                    z = float(target_pos['z'])
                else:
                    print(f"Unknown Format: {target_pos}")
                    continue

                bot.move_to_xyz(x, y, z, duration_ms=1000)
                
            except Exception as e:
                print(f"Move Error: {e}")

        with shared.state_lock:
            shared.robot_state["x"] = bot.last_pos[0]
            shared.robot_state["y"] = bot.last_pos[1]
            shared.robot_state["z"] = bot.last_pos[2]
            
            if hasattr(bot, 'last_joints'):
                degrees = [math.degrees(rad) for rad in bot.last_joints]
                shared.joints_degrees = degrees[1:6]

        time.sleep(0.05)
