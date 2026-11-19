from fastapi import APIRouter
from api.schemas import MessageInput
from api.service import create_request, list_requests, get_request 


router = APIRouter(prefix="/enclosure", tags=["enclosure"])


@router.post("/library-requests", status_code=201)
def create_enclosure_request(body: MessageInput) -> dict:
    return create_request(body)


@router.get("/library-requests")
def list_enclosure_requests() -> list[dict]:
    return list_requests()


@router.get("/library-requests/{request_id}")
def get_enclosure_request(request_id: int) -> dict:
    return get_request(request_id)