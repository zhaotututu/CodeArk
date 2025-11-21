from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.logger import manager

router = APIRouter()

@router.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
            # We don't expect client messages, just keep alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.websocket("/ws/projects/{project_id}")
async def websocket_project_logs(websocket: WebSocket, project_id: int):
    await manager.connect(websocket, project_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id)

