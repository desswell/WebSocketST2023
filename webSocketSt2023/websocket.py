import asyncio
import json
import grpc
import websockets
import not_pb2
import not_pb2_grpc
connected = set()
disconnected = set()
message_cache = []
connected_user_id = {}

async def websocket_handler(websocket):
    print('ws handler')
    connected.add(websocket)
    try:
        while True:
            message = await websocket.recv()
            message = json.loads(message)
            print(connected_user_id)
            if len(message.keys()) == 1:
                connected_user_id[websocket] = message["id"]
                print(connected_user_id)
            else:
                print(f"Received message: {message}")
                with grpc.insecure_channel('localhost:7000') as channel:
                    stub = not_pb2_grpc.send_notificationsStub(channel=channel)
                    response = stub.sendNotifications(not_pb2.notifications(data=[message]))
    except websockets.exceptions.ConnectionClosed:
        print("WebSocket connection closed")
        disconnected.add(websocket)
    finally:
        if connected_user_id:
            del connected_user_id[websocket]
        connected.remove(websocket)


async def send_to_broken():
    successful_connection = set()
    for message in message_cache:
        for client in disconnected:
            try:
                client.send(str(message)[2: -1])
                successful_connection.add(client)
            except ConnectionRefusedError:
                continue

    for client in successful_connection:
        connected.add(client)
        disconnected.remove(client)


async def start_websocket_server():
    print('start ws')

    async with websockets.serve(websocket_handler, 'localhost', 9000):
        print('9000 started')
        await asyncio.Future()


async def handle_grpc(reader, writer):
    print('handle grpc')

    data = await reader.read(1024)
    print(data)
    message_cache.append(data)
    if len(message_cache) == 31:
        del message_cache[0]

    await send_data_via_websocket(data=data)
    writer.close()


async def start_grpc_server():
    print('start grpc')
    server = await asyncio.start_server(handle_grpc, 'localhost', 9020)

    async with server:
        print('9020 started')
        await server.serve_forever()


async def send_data_via_websocket(data):
    for connection in connected:
        await connection.send(str(data)[2: -1])


async def run_websocket_server():
    print('run_ws')
    await start_websocket_server()


async def start_servers_concurrently():
    print(2)

    server_grpc = asyncio.create_task(start_grpc_server())
    server_ws = asyncio.create_task(start_websocket_server())

    await asyncio.gather(server_grpc, server_ws)

if __name__ == "__main__":
    print('run')
    main_loop = asyncio.get_event_loop()
    main_loop.run_until_complete(start_servers_concurrently())
    main_loop.run_forever()