import socketio
import threading
import time
import requests
import logging
from shared.config import GlobalConfig

class PyBulletClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PyBulletClient, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized: return
        self.sio = socketio.Client()
        self.server_url = GlobalConfig.SIM_SERVER_URL
        self.connected = False
        self.latest_state = {}
        self.lock = threading.Lock()
        
        # Callbacks
        self.sio.on('connect', self.on_connect)
        self.sio.on('disconnect', self.on_disconnect)
        self.sio.on('robot_state', self.on_robot_state)
        self.sio.on('object_state', self.on_object_state)
        
        self.initialized = True

    def connect(self):
        if self.connected: return
        try:
            logging.info(f"[PyBullet] Connecting to {self.server_url}...")
            self.sio.connect(self.server_url)
            self.connected = True
        except Exception as e:
            logging.error(f"[PyBullet] Connection failed: {e}")

    def on_connect(self):
        logging.info("[PyBullet] Connected to Simulation Server")
        self.connected = True

    def on_disconnect(self):
        logging.info("[PyBullet] Disconnected")
        self.connected = False

    def on_robot_state(self, data):
        with self.lock:
            self.latest_state['robot'] = data

    def on_object_state(self, data):
        with self.lock:
            self.latest_state['object'] = data

    # Command Methods matching README protocol
    
    def set_joints(self, joints: list):
        if not self.connected: return
        self.sio.emit('set_joints', {'joints': joints})

    def set_pos(self, pos: list):
        """ pos: [x, y, z] """
        if not self.connected: return
        self.sio.emit('set_pos', {'pos': pos})

    def set_gripper(self, value: float):
        """ value: 0.0 ~ 0.06 """
        if not self.connected: return
        self.sio.emit('set_gripper', {'gripper': value})

    def set_object(self, op="create", obj_type="duck", fix=False):
        if not self.connected: return
        self.sio.emit('set_object', {'op': op, 'object': obj_type, 'fix': fix})

    # Video Proxy (MJPEG)
    def get_video_stream(self):
        """ Generator for PyBullet Video Stream (Proxy) """
        try:
            # Connect to PyBullet MJPEG stream and yield chunks
            resp = requests.get(f"{self.server_url}/", stream=True, timeout=5)
            for chunk in resp.iter_content(chunk_size=1024):
                yield chunk
        except Exception as e:
            logging.error(f"[PyBullet] Video Proxy Error: {e}")
            # Yield error frame or stop
            return

pybullet_client = PyBulletClient()