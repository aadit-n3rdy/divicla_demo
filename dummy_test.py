import asyncio
import websockets
import random
import sys

alive = True
bench = False

async def test_websocket():
    uri = "ws://localhost:6000"
    # node_id = "test_node"
    node_id = sys.argv[1]

    async def receive_messages(websocket):
        global alive, bench
        while True:
            message = await websocket.recv()
            print(f"Received: {message}")
            if message == "START":
                alive = not alive
            elif message == "BENCH":
                bench = not bench

    # Start a separate task to receive messages

    async with websockets.connect(uri) as websocket:

        asyncio.create_task(receive_messages(websocket))
        # Send the node ID to the server
        await websocket.send(node_id)
        print(f"Connected as {node_id}")

        # Send test messages

        while True:
            randutil = random.random()*100
            await websocket.send(f'{randutil},{int(alive)},{int(bench)}')
            # print(f"Sent {randutil}, 1, 1")
            await asyncio.sleep(1)  # Wait for 1 second between messages

# Run the test
asyncio.run(test_websocket())