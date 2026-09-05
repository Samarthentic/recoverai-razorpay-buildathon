import uuid
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Payment
from app.schemas import AnalysisResponse, AIRecommendation, PolicyDecisionOut
from app.services.batch_processor import process_single_payment
from app.services.policy_engine import create_policy_config_from_settings
from app.config import get_settings

router = APIRouter()

@router.post("/analyze/{payment_id}", response_model=AnalysisResponse)
def analyze_single_payment(payment_id: str, db: Session = Depends(get_db)):
    """Analyze a single payment and run the recovery pipeline on it."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    batch_id = f"single_{uuid.uuid4().hex[:10]}"
    settings = get_settings()
    policy_config = create_policy_config_from_settings(settings)
    
    result = process_single_payment(db, payment, batch_id, policy_config, settings)
    db.commit()

    ai_rec = AIRecommendation(
        root_cause=result.ai_root_cause or "",
        recommendation=result.ai_recommendation or "",
        confidence=result.ai_confidence or 0.0,
        explanation=result.ai_explanation or "",
        is_recoverable=result.ai_is_recoverable if result.ai_is_recoverable is not None else False
    )

    policy_reasons = []
    if result.policy_reasons:
        try:
            policy_reasons = json.loads(result.policy_reasons)
        except json.JSONDecodeError:
            policy_reasons = []

    policy_decision = PolicyDecisionOut(
        decision=result.policy_decision or "",
        triggered_rules=policy_reasons,
        reasons=[]
    )
    
    return AnalysisResponse(
        payment=payment,
        ai_recommendation=ai_rec,
        policy_decision=policy_decision,
        action_taken=result.action_taken or "none",
        recovery_successful=result.recovery_successful,
        amount_recovered=result.amount_recovered or 0
    )
