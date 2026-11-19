from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.schemas import MessageIn, WorkshopOrderOut
from api.service import create_order, list_orders, get_order
from db.session import get_db

router = APIRouter(
    prefix="/workshop-orders",
    tags=["workshop-orders"],
)

@router.post("", status_code=201, response_model=WorkshopOrderOut)
async def create_workshop_order(
    body: MessageIn,
    db: Session = Depends(get_db),
):
    return await create_order(db, body.message)

@router.get("", response_model=list[WorkshopOrderOut])
def read_workshop_orders(db: Session = Depends(get_db)):
    return list_orders(db)

@router.get("/{order_id}", response_model=WorkshopOrderOut)
def read_workshop_order(
    order_id: int,
    db: Session = Depends(get_db),
):
    return get_order(db, order_id)
