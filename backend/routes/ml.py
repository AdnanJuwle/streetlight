"""
API routes for ML predictions
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from models.database import get_session, MLPrediction
from schemas import MLPredictionResponse
from sqlalchemy import desc

router = APIRouter(prefix="/api/v1/ml", tags=["ml"])


def get_db():
    """Dependency for database session"""
    from models.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/predictions/{device_id}", response_model=List[MLPredictionResponse])
async def get_predictions(
    device_id: str,
    prediction_type: str = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get ML predictions for a device"""
    query = db.query(MLPrediction).filter(MLPrediction.device_id == device_id)
    
    if prediction_type:
        query = query.filter(MLPrediction.prediction_type == prediction_type)
    
    predictions = query.order_by(desc(MLPrediction.timestamp)).limit(limit).all()
    return predictions


@router.get("/predictions/{device_id}/latest", response_model=MLPredictionResponse)
async def get_latest_prediction(
    device_id: str,
    prediction_type: str = None,
    db: Session = Depends(get_db)
):
    """Get latest ML prediction for a device"""
    query = db.query(MLPrediction).filter(MLPrediction.device_id == device_id)
    
    if prediction_type:
        query = query.filter(MLPrediction.prediction_type == prediction_type)
    
    prediction = query.order_by(desc(MLPrediction.timestamp)).first()
    
    if not prediction:
        raise HTTPException(status_code=404, detail="No predictions found")
    
    return prediction

