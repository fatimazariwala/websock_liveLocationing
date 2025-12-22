#!/usr/bin/env python

import asyncio
import aiomysql
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

DB_CONFIG = {
    "host": "localhost",   
    "port": 3306,         
    "user": "kamailio",  
    "password": "kamailiorw", 
    "db": "kamailio", 
}


JOIN = {}

async def delete_from_database(join_key):
    print(f"in delete {join_key}")
    try:
        conn = await aiomysql.connect(**DB_CONFIG)
        async with conn.cursor() as cur:
            await cur.execute("DELETE FROM websock WHERE joinkey = %s", (join_key,))
            await conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database error (DELETE): {e}")

async def save_to_database(join_key):
    try:
        conn = await aiomysql.connect(**DB_CONFIG)
        async with conn.cursor() as cur:
            await cur.execute("INSERT INTO websock (joinkey) VALUES (%s)", (join_key,))
            await conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database error (INSERT): {e}")

async def exists(join_key):
    if join_key in JOIN:
        return True

    try:
        conn = await aiomysql.connect(**DB_CONFIG)
        async with conn.cursor() as cur:
            await cur.execute("SELECT joinkey FROM websock WHERE joinkey = %s", (join_key,))
            row = await cur.fetchone() 
        conn.close()

        if row:
            JOIN[join_key] = [] 
            return True
    except Exception as e:
        print(f"Database error (EXISTS): {e}")

    return False

async def notify_other_clients(join_key, message,person):
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
        print(f"intrnsmit {event_received}")
        if event_received["type"] == "Location Data":
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
                        
        elif event_received["type"] == "destroy":
            print("in destory event")
            join_key = event_received["join"]
            await delete_from_database(join_key)
            if join_key in JOIN:
                await notify_other_clients(join_key,f"{join_key} Session Destroyed!","")
                del JOIN[join_key]
            

async def error(websocket, message):
    event = {
        "type": "error",
        "message": message,
    }
    await websocket.send(json.dumps(event))

async def join(websocket, join_key, person):
    conn = {"person": person, "ws": websocket}
    if await exists(join_key):   
        JOIN[join_key].append(conn)
        try:
            print("Joined!", join_key)
            await notify_other_clients(join_key, f"{person} Joined!",person)
            await transmit(websocket, join_key)
        finally:
            if join_key in JOIN:
                JOIN[join_key].remove(conn)
                await notify_other_clients(join_key, f"{person} Disconnected!",person)
    else:
        print(f"Join Key Not Found: {join_key}")
        await error(websocket, "Join Key Not Found!")

async def start(websocket, person):
    join_key = secrets.token_urlsafe(10)
    conn = {"person": person, "ws": websocket}
    JOIN[join_key] = [conn]  
    await save_to_database(join_key)
    print(f"New Connection with join id: {join_key}")
    
    try:
        event = {
            "type": "init",
            "join": join_key,
        }
        await websocket.send(json.dumps(event))
        await transmit(websocket, join_key)
    finally:
        if join_key in JOIN:
            JOIN[join_key].remove(conn)
            await notify_other_clients(join_key, f"{person} Disconnected!",person)

async def handler(websocket):
    try:
        message = await websocket.recv()
        event = json.loads(message)
        print(event)

        if event.get("type") == "init" and "join" not in event:
            await start(websocket, event["person"])
        elif event.get("type") == "init" and "join" in event:
            await join(websocket, event["join"], event["person"])
        else:
            print(f"Invalid message format: {event}")
            await error(websocket, "Invalid message format.")
    except (ConnectionClosedOK, ConnectionClosedError):
        print("Connection closed unexpectedly.")

async def main():
    async with serve(handler, "0.0.0.0", 8001): 
        await asyncio.Future()  

if __name__ == "__main__":
    asyncio.run(main())


 # {"type":"play","player":"PLAYER1","column":0,"row":0}
   # {"type":"Location Data","person":"fatima","latitude":72.3456789,"longitude":122.3456789}
