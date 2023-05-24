import asyncio
import json
import time

import grpc
import websockets
import not_pb2
import not_pb2_grpc
connected = set()
disconnected = set()
message_cache = []
connected_user_login = {}
global_message = [0]
async def websocket_handler(websocket):
    print('ws handler')
    connected.add(websocket)
    try:
        while True:
            with grpc.insecure_channel('localhost:7010') as channel:
                message = await websocket.recv()
                message = json.loads(message)
                print(connected_user_login)
                if len(message.keys()) == 1:
                    connected_user_login[websocket] = message["login"]
                    print(connected_user_login)
                else:
                    print(f"Received message: {message}")
                    global_message[0] = message["id"]
                    stub = not_pb2_grpc.send_notificationsStub(channel=channel)
                    response = stub.sendNotifications(not_pb2.notifications(data=[message]))
    except websockets.exceptions.ConnectionClosed:
        print("WebSocket connection closed")
        disconnected.add(websocket)
    finally:
        if connected_user_login:
            del connected_user_login[websocket]
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
    data = data.decode('utf-8')
    data = data[1:]
    data = data[:-1]
    data = json.loads(data)
    username = data['username']
    reverseConnected_user_login = dict(zip(connected_user_login.values(), connected_user_login.keys()))
    connection = reverseConnected_user_login.get(username)
    data_to_send = str(global_message[0])
    print(data_to_send)
    if data_to_send:
        await connection.send(data_to_send)
        time.sleep(1)


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