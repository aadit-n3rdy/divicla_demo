import asyncio
import websockets
import threading
import streamlit as st
import time
import pandas as pd
import socket
import plotly.express as px

class Data:
    def __init__(self):
        self.util = pd.DataFrame({"time": [], "util": []})
        # self.util = 0.0
        self.alive = False
        self.bench = False
        self.start = time.time()
    def add(self, util, alive, bench):
        self.util = pd.concat([self.util, pd.DataFrame({"time": [time.time() - self.start], "util": [util]})], ignore_index=True).tail(50)
        # self.util = util
        self.alive = alive
        self.bench = bench


async def handler(websocket):
    print("RUNNING HANDLER")
    nodeId = await websocket.recv()
    print(f"Connected: {nodeId}")
    st.session_state.connDict[nodeId] = websocket
    st.session_state.stateDict = st.session_state.stateDict
    if nodeId not in st.session_state.stateDict:
        st.session_state.stateDict[nodeId] = Data()
    while True:
        msg = await websocket.recv()
        util, alive, bench = msg.split(",")
        util = float(util)
        alive = bool(int(alive))
        bench = bool(int(bench))
        st.session_state.stateDict[nodeId].add(util, alive, bench)
        
def toggleBench(nodeId):
    print("Toggling bench for ", nodeId)
    try:
        if nodeId in st.session_state.connDict:
            websocket = st.session_state.connDict[nodeId]
            state = st.session_state.stateDict[nodeId].bench
            if state:
                print("Sending")
                asyncio.run(websocket.send("BENCH_STOP"))
                print(f"Sent to {nodeId}: BENCH_STOP")
            else:
                print("Sending")
                asyncio.run(websocket.send("BENCH_START"))
                print(f"Sent to {nodeId}: BENCH_START")
    except Exception as e:
        print(e)

def toggleStart(nodeId):
    try:
        print("Toggling start for ", nodeId)
        if nodeId in st.session_state.connDict:
            websocket = st.session_state.connDict[nodeId]
            state = st.session_state.stateDict[nodeId].alive
            if state:
                print("Sending")
                asyncio.run(websocket.send("START"))
                print(f"Sent to {nodeId}: START")
            else:
                print("Sending")
                asyncio.run(websocket.send("STOP"))
                print(f"Sent to {nodeId}: STOP")
    except Exception as e:
        print(e)

async def wsmain():
    print("RUNNING WSMAIN")
    try:
        server = await websockets.serve(handler, "localhost", 5763)
        print("WebSocket server started on ws://localhost:5763")
        await server.wait_closed()
    except Exception as e:
        print(f"Error starting WebSocket server: {e}")

def streamlit_app():
    print("Starting STREAMLIT")

    if 'connDict' not in st.session_state:
        st.session_state.connDict = {}
        print("added connDict")
    if 'stateDict' not in st.session_state:
        print("added stateDict")
        st.session_state.stateDict = {}
    if 'placeholders' not in st.session_state:
        print("added placeholders")
        st.session_state.placeholders = {}

    if 'websocket_thread' not in st.session_state:
        websocket_thread = threading.Thread(target=lambda: asyncio.run(wsmain()), daemon=True)
        websocket_thread.start()

    time.sleep(1)

    st.title("Dynamic Offloading")
    st.write("This demo shows the CPU utilization of two nodes dynamically offloading a video classification workload")

    col1, col2 = st.columns(2)
    p1 = None
    p2 = None
    with col1:
        st.markdown("## Node 1")
        startButton = st.toggle("Running ", key=f"start_node1", on_change=toggleStart, args=("node1",), value=True)
        # sb = st.button("Start Node 1", key="start_node1", on_click=toggleStart, args=("node1",), disabled=False)
        # bb = st.button("Benchmark Node 1", key="bench_node1", on_click=toggleBench, args=("node1",), disabled=False)
        benchButton =  st.toggle("Benchmark", key=f"bench_node1", on_change=toggleBench, args=("node1",), value=False)
        p1 = st.empty()
    with col2:
        st.markdown("## Node 2")
        startButton = st.toggle("Running ", key=f"start_node2", on_change=lambda: toggleStart("node2"), value=True)
        benchButton =  st.toggle("Benchmark", key=f"bench_node2", on_change=lambda: toggleBench("node2"), value=False)
        p2 = st.empty()

    p = st.empty()

    while True:
        with p:
            st.write(st.session_state)
        try:
            stateDict = st.session_state.stateDict
            print(stateDict.keys())
            print("UPDATING")
            if "node1" in stateDict:
                print("Found node1")
                with p1:
                    pxchart = px.line(stateDict["node1"].util, x="time", y="util", title=f"CPU Utilization for node1")
                    st.plotly_chart(pxchart)
            if "node2" in stateDict:
                print("Found node2")
                with p2:
                    pxchart = px.line(stateDict["node2"].util, x="time", y="util", title=f"CPU Utilization for node2")
                    st.plotly_chart(pxchart)
        except Exception as e:
            print("Exception while updating: ", e)
        time.sleep(1)

if __name__ == "__main__":
    # Run the WebSocket server in a separate thread
    # Run the Streamlit app
    streamlit_app()