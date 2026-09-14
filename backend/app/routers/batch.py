import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuditLog, BatchRun, Payment, RecoveryResult
from app.schemas import BatchResetOut, BatchRunOut, RecoveryResultOut
from app.services.batch_processor import run_batch
from app.config import get_settings

router = APIRouter()

@router.post("/batch/run", response_model=BatchRunOut)
def run_batch_analysis(db: Session = Depends(get_db)):
    """Run batch analysis on all failed payments."""
    active_batch = db.query(BatchRun).filter(BatchRun.status == "running").first()
    if active_batch:
        raise HTTPException(
            status_code=409,
            detail=f"Batch run {active_batch.id} is already in progress."
        )
    settings = get_settings()
    batch = run_batch(db, settings)
    return batch

@router.post("/batch/reset", response_model=BatchResetOut)
def reset_batch_analysis(db: Session = Depends(get_db)):
    """Reset current recovery analysis artifacts while preserving all payments."""
    active_batch = db.query(BatchRun).filter(BatchRun.status == "running").first()
    if active_batch:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot reset while batch run {active_batch.id} is in progress."
        )
    db.query(RecoveryResult).delete()
    db.query(AuditLog).delete()
    db.query(BatchRun).delete()
    db.commit()

    payment_count = db.query(Payment).count()
    return BatchResetOut(
        status="reset",
        state="ready",
        payment_count=payment_count,
        batch_id=None,
    )

@router.get("/batch/{batch_id}", response_model=BatchRunOut)
def get_batch(batch_id: str, db: Session = Depends(get_db)):
    """Get details of a specific batch run."""
    batch = db.query(BatchRun).filter(BatchRun.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch run not found")
    return batch

@router.get("/batch", response_model=list[BatchRunOut])
def list_batches(db: Session = Depends(get_db)):
    """List all batch runs, most recent first."""
    return db.query(BatchRun).order_by(BatchRun.started_at.desc()).all()

@router.get("/batch/{batch_id}/results", response_model=list[RecoveryResultOut])
def get_batch_results(batch_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all recovery results for a specific batch run."""
    results = db.query(RecoveryResult).filter(RecoveryResult.batch_id == batch_id).offset(skip).limit(limit).all()
    
    # Need to process policy_reasons from string to list before returning since schema expects a list
    processed_results = []
    for result in results:
        res_dict = {c.name: getattr(result, c.name) for c in result.__table__.columns}
        if res_dict.get('policy_reasons'):
            try:
                res_dict['policy_reasons'] = json.loads(res_dict['policy_reasons'])
            except json.JSONDecodeError:
                res_dict['policy_reasons'] = []
        else:
            res_dict['policy_reasons'] = []
        processed_results.append(res_dict)
        
    return processed_results
