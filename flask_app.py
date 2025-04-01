from flask import Flask, render_template
from flask_socketio import SocketIO
import psutil
import threading
import asyncio
from websockets.sync.server import serve
import time
import json

app = Flask(__name__)
socketio = SocketIO(app)

# Serve the webpage
@app.route('/')
def index():
    return render_template('index.html')

class Data:
    def __init__(self, conn):
        self.time = time.time()
        self.util = 0.0
        self.alive = False
        self.bench = False
        self.conn = conn
    def add(self, util, alive, bench):
        self.time = time.time()
        self.util = util
        self.alive = alive
        self.bench = bench

stateDict = {}

# WebSocket server to emit CPU utilization data
def emit_cpu_utilization():
    while True:
        state = {}
        for k, v in stateDict.items():
            state[k] = {
                "util": v.util,
                "alive": v.alive,
                "bench": v.bench
            }
        socketio.emit('cpu_update', json.dumps(state))
        time.sleep(1)

emitThread = threading.Thread(target=emit_cpu_utilization)
emitThread.daemon = True
emitThread.start()

@socketio.on("control")
def handleToggle(msg):
    msg = json.loads(msg)
    nodeId = msg["node"]
    cmd = msg["cmd"]
    print(f"Received command {cmd} for {nodeId}")
    stateDict[nodeId].conn.send(cmd)
    print(f"Sent {cmd} to {nodeId}")

def handler(websocket):
    print("New conn")
    nodeId = websocket.recv()
    print(f"Connected: {nodeId}")
    stateDict[nodeId] = Data(websocket)
    while True:
        msg = websocket.recv()
        util, alive, bench = msg.split(",")
        util = float(util)
        alive = bool(int(alive))
        bench = bool(int(bench))
        stateDict[nodeId].add(util, alive, bench)

# Start the WebSocket server
def start_websocket_server():
    srv = serve(handler, "", 6000)
    print("Starting WebSocket server")
    srv.serve_forever()
    print("This shouldn't print")

# Start both Flask and WebSocket servers in separate threads
if __name__ == '__main__':
    threading.Thread(target=start_websocket_server, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5000)