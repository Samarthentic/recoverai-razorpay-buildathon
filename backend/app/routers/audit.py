from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuditLog
from app.schemas import AuditLogOut

router = APIRouter()

@router.get("/audit", response_model=list[AuditLogOut])
def list_audit_logs(
    payment_id: str | None = None, 
    event_type: str | None = None, 
    batch_id: str | None = None, 
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """List audit logs with optional filters and pagination."""
    query = db.query(AuditLog)
    
    if payment_id:
        query = query.filter(AuditLog.payment_id == payment_id)
    if event_type:
        query = query.filter(AuditLog.event_type == event_type)
    if batch_id:
        query = query.filter(AuditLog.batch_id == batch_id)
        
    return query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/audit/payment/{payment_id}", response_model=list[AuditLogOut])
def get_payment_audit(payment_id: str, db: Session = Depends(get_db)):
    """Get all audit logs for a specific payment, ordered by creation time."""
    return db.query(AuditLog).filter(AuditLog.payment_id == payment_id).order_by(AuditLog.created_at.asc()).all()
