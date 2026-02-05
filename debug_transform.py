
import pybullet as p
import numpy as np
import time

def debug():
    try:
        cid = p.connect(p.SHARED_MEMORY)
        if cid < 0:
            print("Failed to connect to shared memory. Is the sim running?")
            return
    except:
        print("Error connecting")
        return

    # Check robots
    robots = [i for i in range(p.getNumBodies())]
    if not robots:
        print("No bodies found")
        return
    
    # Assuming Robot is index 0 or 'robot' name.
    # We will search for 'panda' or similar, or just take the first robot.
    robot_id = 0 # Usually 0 in this setup
    
    # 1. Get EE Pose (Index 11 usually for Panda Tip, logic says 'end_effector_link')
    # Use generic method? Better to rely on what pybullet_sim.py uses.
    # But for a quick check, let's list joints
    num_joints = p.getNumJoints(robot_id)
    ee_idx = num_joints - 1 # Approx
    
    # Find joint named 'ee' or 'tip'
    for i in range(num_joints):
        info = p.getJointInfo(robot_id, i)
        name = info[1].decode('utf-8')
        if 'ee' in name or 'tip' in name or 'grasp' in name:
            ee_idx = i
            print(f"Found EE Link: {name} (ID: {i})")
            # break # Don't break, find last one usually
            
    state = p.getLinkState(robot_id, ee_idx, computeForwardKinematics=True)
    pos = state[4] # worldLinkFramePosition
    orn = state[5] # worldLinkFrameOrientation
    
    print(f"\n[Robot EE State]")
    print(f"Pos (m): {pos}")
    print(f"Orn (q): {orn}")
    
    # Matrix
    rot = p.getMatrixFromQuaternion(orn)
    rot_mat = np.array(rot).reshape(3, 3)
    print(f"Rotation Matrix:\n{rot_mat}")
    
    # Verify 'Down' Vector
    # Z-axis of EE frame in World coords
    z_axis = rot_mat[:, 2] # Column 2
    print(f"EE Z-axis World Vector: {z_axis}")
    # If looking down, Z-axis should be (0, 0, -1) or close.
    
    # 2. Simulate Transformation
    print("\n[Simulation]")
    depth_cm = 20.0
    point_view = [0, 0, -depth_cm] # Straight ahead (or down) in camera view
    
    # Current code logic:
    # p_local = np.array([-point_view[1], -point_view[0], -point_view[2]])
    p_local = np.array([-point_view[1], -point_view[0], -point_view[2]])
    print(f"p_local (Code Logic): {p_local}") 
    # expected: [0, 0, 20] if -point_view[2] = 20
    
    t_world = np.array(pos) * 100.0
    p_world = rot_mat @ p_local + t_world
    
    print(f"Robot Z (cm): {t_world[2]:.2f}")
    print(f"Result World Z (cm): {p_world[2]:.2f}")
    
    delta_z = p_world[2] - t_world[2]
    print(f"Delta Z: {delta_z:.2f} (Should be negative ~ -20 for looking down)")
    
    if delta_z > 0:
        print("FAIL: The vector points UP!")
    else:
        print("SUCCESS: The vector points DOWN.")

    p.disconnect()

if __name__ == "__main__":
    debug()
