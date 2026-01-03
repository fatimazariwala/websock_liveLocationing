# WebSocket Room-Based Communication Server (Python)

## 📌 Overview

This project implements a **custom, asynchronous WebSocket server in Python** that supports **room-based (key-based) real-time communication**.

Each client joins the server using a **room key**, which logically groups multiple users into the same communication session. Messages sent by a user are broadcast **only to other users within the same room**, ensuring isolation and efficient routing.

### In Simple Terms

* Each **key represents a room**
* Multiple users can join the same room
* Messages are shared only among users in the same room

---

## Use Cases

This architecture is well-suited for:

* Real-time chat applications
* Emergency response and coordination systems
* Live location sharing
* Multiplayer or collaborative applications
* IoT command-and-control dashboards

---

## Core Data Structure

Active WebSocket connections are maintained in-memory using the following structure:

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

### Structure Explanation

* **Key (string)** → Unique room identifier
* **Value (list)** → Active users connected to that room

Each user entry contains:

* `name`: Unique identifier of the user within the room
* `ws`: Active WebSocket connection object

➡️ Users joining with the same room key are placed in the same list and can communicate with each other.

---

## 🔄 Connection Lifecycle

### 1. Client Connection

When a client connects, it provides:

* `username`
* `room_key`

---

### 2. Room Join Logic

```python
if await exists(join_key):   
    JOIN[join_key].append(conn)
```

* If the `room_key` exists:

  * The user is added to the room
* If the key does **not** exist:

  * The user is notified that no active session is available

#### `exists(join_key)` Logic

1. Check the in-memory `JOIN` structure
2. If not found, query the database
3. If found in the database:

   * Restore the room key in `JOIN`
4. If not found anywhere:

   * Reject the join request

---

## Message Broadcasting

Messages are broadcast **only within the same room**.

```python
if join_key in JOIN:
    for conn in JOIN[join_key]:
        if conn["person"] != person:
            await conn["ws"].send(json.dumps(complete_message))
```

### Key Points

* Messages are **not echoed back** to the sender
* Communication is fully isolated between rooms
* The `person` field acts as a **unique identifier per user**
* Uniqueness of `person` is enforced at the client level

---

## Disconnect Handling

Disconnects can occur due to:

* App closure
* Network failure
* Unexpected client crash

These are handled safely using a `finally` block in the `join()` lifecycle.

```python
finally:
    if join_key in JOIN:
        JOIN[join_key].remove(conn)
        await notify_other_clients(join_key, f"{person} Disconnected!", person)
```

### Why This Works

* WebSocket disconnections are **implicit**
* The `finally` block executes regardless of how the connection ends
* Ensures:

  * No stale connections
  * Proper user cleanup
  * Accurate room state

---

## Persistence & Backup (MariaDB)

WebSocket connections are **in-memory** and are lost on server restarts. To ensure fault tolerance, **room keys are persisted in a MariaDB database**.

> User details are not stored in the database and are managed entirely on the client side.

### Stored Data

* `room_key` (Primary identifier)
* Optional metadata (creation time, owner, status)

### Recovery Flow

```python
async def exists(join_key):
    if join_key in JOIN:
        return True

    try:
        conn = await aiomysql.connect(**DB_CONFIG)
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT joinkey FROM websock WHERE joinkey = %s",
                (join_key,)
            )
            row = await cur.fetchone()
        conn.close()

        if row:
            JOIN[join_key] = []
            return True
    except Exception as e:
        print(f"Database error (EXISTS): {e}")

    return False
```

---

## Step-by-Step Usage Guide

### 1. Download the Project

```bash
git clone <repository-url>
cd <project-directory>
```

---

### 2. Install Required Python Dependencies

```bash
pip install websockets aiomysql
```

> `asyncio`, `json`, and `secrets` are included in the Python standard library.

---

### 3. Set Up MariaDB

```sql
CREATE DATABASE <your_db_name>;

CREATE TABLE websock (
    joinkey VARCHAR(255) PRIMARY KEY
);
```

Configure `DB_CONFIG` with matching credentials.

`DB_CONFIG = {
    "host": "localhost",
    "user": "<your_db_username>",
    "password": "<your_db_password>",
    "db": "<ypur_db_name>"
}`


---

### 4️⃣ Run the Server

```bash
python3 live_location.py
```

---

### 5️⃣ Create a New Room

Connect to:

```
ws://<server_ip>:<port>
```

Send:

```json
{
  "type": "init",
  "person": "<user_unique_identifier>"
}
```

The server responds with a generated **room key**.

---

### 6️⃣ Join an Existing Room

```json
{
  "type": "init",
  "person": "<user_unique_identifier>",
  "join": "<existing_room_key>"
}
```

---

## Technologies Used

* Python 3.x
* asyncio
* WebSockets
* MariaDB

---

## Future Enhancements

* Authentication and authorization
* Redis-backed room persistence
* Message history
* TLS-secured WebSocket connections

---

## 👤 Author

**Fatima Zariwala**

---

## 📄 License

This project is intended for educational and research purposes.
