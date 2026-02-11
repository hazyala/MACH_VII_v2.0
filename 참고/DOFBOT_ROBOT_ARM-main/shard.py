import threading

frame_lock = threading.Lock()
state_lock = threading.Lock()
cmd_lock = threading.Lock()

latest_frame = None
latest_frame_depth = None

robot_state = {"x": 0.0, "y": 0.0, "z": 0.0}
joints_degrees = [0, 0, 0, 0, 0]

object_info = {
    "exists": False,
    "x": 0.0, "y": 0.0, "z": 0.0,
    "distance": 0.0
}

command = {
    "target_pos": None,
    "joint_cmd": None,
    "gripper_cmd": None,
    "force": 100,
    "max_velocity": 100,
    "object_cmd": None,
    "object_pos_cmd": None
}
