"""
Real-time Performance Updates WebSocket
"""
from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.educator import Educator
from app.api.performance_views import get_overall_performance
import json
import asyncio
from typing import List

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.educator_connections: dict = {}  # educator_id -> [websockets]

    async def connect(self, websocket: WebSocket, educator_id: int):
        await websocket.accept()
        self.active_connections.append(websocket)
        
        if educator_id not in self.educator_connections:
            self.educator_connections[educator_id] = []
        self.educator_connections[educator_id].append(websocket)

    def disconnect(self, websocket: WebSocket, educator_id: int = None):
        self.active_connections.remove(websocket)
        if educator_id and educator_id in self.educator_connections:
            self.educator_connections[educator_id].remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast_to_educator(self, message: str, educator_id: int):
        if educator_id in self.educator_connections:
            for connection in self.educator_connections[educator_id]:
                try:
                    await connection.send_text(message)
                except:
                    # Remove dead connections
                    self.educator_connections[educator_id].remove(connection)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                self.active_connections.remove(connection)

manager = ConnectionManager()

async def get_performance_updates(educator_id: int, db: Session):
    """Get real-time performance updates for an educator"""
    try:
        # Get educator
        educator = db.query(Educator).filter(Educator.id == educator_id).first()
        if not educator:
            return None
            
        # Get updated performance data
        performance_data = await get_overall_performance(current_educator=educator, db=db)
        
        return {
            "type": "performance_update",
            "timestamp": "2025-10-18T12:00:00Z",
            "data": {
                "total_students": performance_data.total_students,
                "overall_average": performance_data.overall_average,
                "overall_pass_rate": performance_data.overall_pass_rate,
                "grade_distribution": performance_data.grade_distribution,
                "subject_performance_chart": performance_data.subject_performance_chart,
                "sections_performance_chart": performance_data.sections_performance_chart,
                "attendance_stats": performance_data.attendance_stats,
                "top_performers_count": len(performance_data.top_performers),
                "low_performers_count": len(performance_data.low_performers)
            }
        }
    except Exception as e:
        print(f"Error getting performance updates: {e}")
        return None

# This function would be called when data changes occur
async def notify_performance_update(educator_id: int):
    """Notify specific educator of performance data changes"""
    db = next(get_db())
    try:
        update_data = await get_performance_updates(educator_id, db)
        if update_data:
            await manager.broadcast_to_educator(
                json.dumps(update_data), 
                educator_id
            )
    except Exception as e:
        print(f"Error notifying performance update: {e}")
    finally:
        db.close()