import threading
import time
from flask import Flask
from flask_socketio import SocketIO
import shared
import robot_thread

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

def broadcast_data():
    while True:
        robot_packet = {}

        with shared.state_lock:
            robot_packet['ee'] = shared.robot_state.copy()
            robot_packet['joints'] = shared.joints_degrees[:]

        try:
            socketio.emit('robot_state', robot_packet)
        except Exception:
            pass
        
        time.sleep(0.05)

@socketio.on('connect')
def handle_connect():
    print(">>> Client Connected")

@socketio.on('set_gripper')
def handle_set_gripper(data):
    if 'gripper' in data:
        with shared.cmd_lock:
            shared.command["gripper_cmd"] = data['gripper']

@socketio.on('set_pos')
def handle_set_pos(data):
    if 'pos' in data:
        with shared.cmd_lock:
            shared.command["target_pos"] = data['pos']

@socketio.on('set_force')
def handle_set_force(data):
    print(f"=== [SERVER] Received Gripper Data: {data} ===")
    if "force" in data:
        with shared.cmd_lock:
            shared.command["force"] = data["force"]
            print(f"=== [SERVER] Shared Command Updated: {shared.command['gripper_cmd']} ===")

@socketio.on('set_max_velocity')
def handle_set_max_velocity(data):
    if 'max_velocity' in data:
        with shared.cmd_lock:
            shared.command["max_velocity"] = data['max_velocity']

if __name__ == "__main__":
    print(">>> System Starting...")

    t_robot = threading.Thread(target=robot_thread.run_robot_loop, daemon=True)
    t_robot.start()

    t_broadcast = threading.Thread(target=broadcast_data, daemon=True)
    t_broadcast.start()

    print(">>> Flask Server & Robot Controller Running...")
    
    #with shared.cmd_lock:
        #shared.command["gripper_cmd"] = 100
        #shared.command["target_pos"] = {"x": 0.10, "y": 0.10, "z": 0.10}
        #print(shared.command["gripper_cmd"]) 
        #print(shared.command["target_pos"])
    
    socketio.run(app, host="0.0.0.0", port=5000, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)
    
