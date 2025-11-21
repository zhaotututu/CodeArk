import asyncio
from typing import List, Dict
from fastapi import WebSocket
from datetime import datetime
import json

class LogManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.project_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, project_id: int = None):
        await websocket.accept()
        if project_id:
            if project_id not in self.project_connections:
                self.project_connections[project_id] = []
            self.project_connections[project_id].append(websocket)
        else:
            self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket, project_id: int = None):
        if project_id and project_id in self.project_connections:
            if websocket in self.project_connections[project_id]:
                self.project_connections[project_id].remove(websocket)
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str, level: str = "info", project_id: int = None):
        payload = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "msg": message,
            "level": level,
            "project_id": project_id
        }
        json_str = json.dumps(payload)
        
        # Global listeners
        for connection in self.active_connections[:]:
            try:
                await connection.send_text(json_str)
            except:
                self.disconnect(connection)
        
        # Project specific listeners
        if project_id and project_id in self.project_connections:
            for connection in self.project_connections[project_id][:]:
                try:
                    await connection.send_text(json_str)
                except:
                    self.disconnect(connection, project_id)

manager = LogManager()

