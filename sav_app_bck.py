#!/usr/bin/env python

import asyncio
import json
import secrets
from websockets.server import serve
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError

# JOIN = {
#     "mcewjfoiwejfio": [
#         {"name": "fat", "ws": "websock"},
#         {"name": "adi", "ws": "websock"}
#     ],
#     "euwjdjwoeoiqi": [
#         {"name": "jedi", "ws": "websock"},
#         {"name": "yda", "ws": "websock"}
#     ]
# }


JOIN = {}

async def re_connect(websocket, join_key, person):
    if join_key in JOIN:
        if any(conn["ws"] == websocket for conn in JOIN[join_key]):
            print("Websocket Already Exists!")
            return
            
        conn = {"person": person, "ws": websocket}
        JOIN[join_key].append(conn)
        try:
            print(f"User From Join Key: {join_key} ReJoined!")
            await notify_other_clients(join_key, f"{person} Connected!",person)
            await transmit(websocket, join_key)
        except (ConnectionClosedOK, ConnectionClosedError):
            await notify_other_clients(join_key, f"{person} Disconnected!",person)
        finally:
            JOIN[join_key].remove(conn)
            if not JOIN[join_key]:  # Check if empty
                del JOIN[join_key]
            else:
                await notify_other_clients(join_key, f"{person} Disconnected!",person)
    else:
        message = f"Join Key: {join_key} NOT Found!"
        await error(websocket, message)

async def notify_other_clients(join_key, message,person):
    """Notify other clients associated with the join_key."""
    print("In Notify_other_clients!")
    complete_message = {
        "type": "connection_message",
        "message": message,
    }
    if join_key in JOIN:
        for conn in JOIN[join_key]:
            if conn["person"] != person:
                try:
                    await conn["ws"].send(json.dumps(complete_message))
                except Exception:
                    print(f"Error Sending Connection Message: {join_key} to {conn['person']}")

async def transmit(websocket, join_key):
    async for message in websocket:
        event_received = json.loads(message)

        event_send = {
            "type": "Location Data",
            "person": event_received["person"],
            "latitude": event_received["latitude"],
            "longitude": event_received["longitude"],
        }
        print(f"Sending Message: {event_send}")
        for conn in JOIN[join_key]:
            if (conn['person'] != event_received["person"]):
                try:
                    await conn["ws"].send(json.dumps(event_send))
                except Exception:
                    print(f"Error Sending Location Data at Key: {join_key}")

async def error(websocket, message):
    event = {
        "type": "error",
        "message": message,
    }
    await websocket.send(json.dumps(event))

async def join(websocket, join_key, person):
    conn = {"person": person, "ws": websocket}
    if join_key in JOIN:
        if any(connz["person"] == person for connz in JOIN[join_key]):
            print(f"{person} Already Joined!")
            return
            
        JOIN[join_key].append(conn)
        event_send = {
            "type": "join",
            "message": f"Joined the Connection using JOIN KEY: {join_key}!"
        }
        try:
            print("Joined!", join_key)
            await notify_other_clients(join_key, f"{person} Joined!",person)
            await transmit(websocket, join_key)
        finally:
            print("In Join Finally!")
            JOIN[join_key].remove(conn)
            if not JOIN[join_key]:
                del JOIN[join_key]
            else:
                await notify_other_clients(join_key, f"{person} Disconnected!",person)
    else:
        print(f"Join Key Not Found: {join_key}")
        await error(websocket, "Join Key Not Found!")

async def start(websocket, person):
    join_key = secrets.token_urlsafe(10)
    conn = {"person": person, "ws": websocket}
    JOIN[join_key] = [conn]  # Initialize as a list
    print(f"New Connection with join id: {join_key}")

    try:
        event = {
            "type": "init",
            "join": join_key,
        }
        await websocket.send(json.dumps(event))
        await transmit(websocket, join_key)
    finally:
        JOIN[join_key].remove(conn)
        if not JOIN[join_key]:
            del JOIN[join_key]
        else:
            await notify_other_clients(join_key, f"{person} Disconnected!",person)

async def handler(websocket):
    try:
        message = await websocket.recv()
        event = json.loads(message)

        if event.get("type") == "init" and "join" not in event:
            await start(websocket, event["person"])
        elif event.get("type") == "init" and "join" in event:
            await join(websocket, event["join"], event["person"])
        elif event.get("type") == "rejoin" and "join" in event:
            await re_connect(websocket, event["join"], event["person"])
        else:
            print(f"Invalid message format: {event}")
            await error(websocket, "Invalid message format.")
    except (ConnectionClosedOK, ConnectionClosedError):
        print("Connection closed unexpectedly.")

async def main():
    async with serve(handler, "0.0.0.0", 8001):  # Bind to all interfaces
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())


 # {"type":"play","player":"PLAYER1","column":0,"row":0}
   # {"type":"Location Data","person":"fatima","latitude":72.3456789,"longitude":122.3456789}
