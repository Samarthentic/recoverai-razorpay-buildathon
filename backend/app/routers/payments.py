from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Payment
from app.schemas import PaymentOut
from app.seed.generate_data import clear_database, seed_database

router = APIRouter()

@router.get("/payments", response_model=list[PaymentOut])
def list_payments(status: str | None = None, skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """List payments with optional status filter and pagination."""
    query = db.query(Payment)
    if status:
        query = query.filter(Payment.status == status)
    return query.offset(skip).limit(limit).all()

@router.get("/payments/demo-cases", response_model=list[PaymentOut])
def get_demo_cases(db: Session = Depends(get_db)):
    """Retrieve the core deterministic demo cases (Cases A-E)."""
    demo_ids = [
        "pay_demo_happy_path",
        "pay_demo_max_retries",
        "pay_demo_high_value",
        "pay_demo_no_email",
        "pay_demo_low_conf",
    ]
    return db.query(Payment).filter(Payment.id.in_(demo_ids)).all()


@router.get("/payments/{payment_id}", response_model=PaymentOut)
def get_payment(payment_id: str, db: Session = Depends(get_db)):
    """Get a single payment by ID."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.post("/payments/seed")
def seed_payments(db: Session = Depends(get_db)):
    """Clear database and re-seed with synthetic payment data."""
    clear_database(db)
    count = seed_database(db)
    return {"message": f"Successfully seeded {count} payments"}
