"""
API Endpoint - Tasks
====================
Poll or check webhook status for long-running Celery tasks.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.models import Task
from backend.dependencies import get_db

router = APIRouter()

@router.get("/{task_id}")
def get_task_status(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    return {
        "task_id": task.task_id,
        "task_type": task.task_type,
        "status": task.status,
        "result": task.result,
        "error": task.error
    }
