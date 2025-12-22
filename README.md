# WebSocket Room-Based Communication Server (Python)

## Overview

This project implements a **custom WebSocket server in Python** that supports **room-based (key-based) communication**. Users are grouped using a shared **room key**, and all users who join with the same key are connected to the same logical socket group (room).

In simple terms:

* Each **key represents a room**
* Multiple users can join the same room
* Messages can be broadcast to all users inside that room

This approach is useful for:

* Real-time chat rooms
* Emergency response coordination
* Live location sharing
* Multiplayer or collaborative applications

---

## Core Data Structure

The server maintains active connections using the following Python data structure:

```python
JOIN = {
    "mcewjfoiwejfio": [
        {"name": "fat", "ws": "websocket_object"},
        {"name": "adi", "ws": "websocket_object"}
    ],
    "euwjdjwoeoiqi": [
        {"name": "jedi", "ws": "websocket_object"},
        {"name": "yda", "ws": "websocket_object"}
    ]
}
```

### Explanation

* **Key (string)** → Unique room identifier
* **Value (list)** → All users connected to that room
* Each user entry contains:

  * `name`: Identifier of the user
  * `ws`: Active WebSocket connection object

If:

* User A joins with key `"xyzzy"`
* User B also joins with key `"xyzzy"`

➡️ Both users are placed in the **same list** and can communicate with each other.

---

## Connection Flow

### 1. Client Connects

* Client sends a WebSocket request
* Provides:

  * `username`
  * `room_key`

### 2. Server Handles Join

* If `room_key` does not exist → create it
* Append the user’s WebSocket object to the room list

```python
if room_key not in JOIN:
    JOIN[room_key] = []

JOIN[room_key].append({
    "name": username,
    "ws": websocket
})
```

---

## Message Broadcasting Logic

Messages sent by a user are broadcast **only to users in the same room**.

```python
for user in JOIN[room_key]:
    if user["ws"] != sender_ws:
        await user["ws"].send(message)
```

This ensures:

* Isolation between rooms
* Efficient message routing

---

## Disconnect Handling

When a user disconnects:

1. Remove them from the room list
2. If the room becomes empty → delete the key

```python
JOIN[room_key] = [u for u in JOIN[room_key] if u["ws"] != websocket]

if not JOIN[room_key]:
    del JOIN[room_key]
```

---

## Why This Design?

### Advantages

* Lightweight and fast
* No external dependencies (manual WebSocket handling)
* Easy to extend (auth, roles, encryption)
* Suitable for real-time systems

### Use Cases

* Emergency response apps
* Group chat systems
* Live tracking dashboards
* IoT command-and-control rooms

---

## Persistence & Backup (MariaDB)

To ensure **fault tolerance and recovery**, all active room keys are also stored in a **MariaDB database**.

### Why Database Backup Is Needed

WebSocket connections are **in-memory**. If the server restarts due to:

* Crash
* Deployment update
* Power/network failure

All active rooms would normally be lost. To avoid this, room keys are persisted in MariaDB.

### What Is Stored

* `room_key` (Primary identifier)
* Optional metadata (creation time, owner, status)

> ⚠️ Note: WebSocket objects themselves cannot be restored, only the **room structure (keys)**.

### Recovery Flow on Server Restart

1. Server starts
2. Previously stored room keys are fetched from MariaDB
3. Empty room structures are recreated in memory
4. Users can safely rejoin their previous rooms

```python
# Example recovery logic
stored_keys = fetch_keys_from_db()

for key in stored_keys:
    JOIN[key] = []
```

### Benefits

* Prevents loss of room metadata
* Enables graceful recovery
* Improves system reliability
* Supports scaling and monitoring

---

## Technologies Used

* Python 3.x
* `asyncio`
* `websockets` (or custom socket handling)

---

## Future Improvements

* Authentication per room
* Room access control
* Redis-backed room persistence
* Message history
* TLS-secured WebSocket connections

---

## Author

Fatima Zariwala

---

## License

This project is for educational and research purposes.
