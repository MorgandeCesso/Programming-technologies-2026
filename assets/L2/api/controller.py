from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.schemas import MessageIn, NoteOut
from api.service import create_note, get_note, list_notes
from db.session import get_db

router = APIRouter(prefix="/enclosure-notes", tags=["enclosure-notes"])


@router.post("", status_code=201, response_model=NoteOut)
async def create_enclosure_note(body: MessageIn, db: Session = Depends(get_db)):
    return await create_note(db, body.message)


@router.get("", response_model=list[NoteOut])
def read_enclosure_notes(db: Session = Depends(get_db)):
    return list_notes(db)


@router.get("/{note_id}", response_model=NoteOut)
def read_enclosure_note(note_id: int, db: Session = Depends(get_db)):
    return get_note(db, note_id)
