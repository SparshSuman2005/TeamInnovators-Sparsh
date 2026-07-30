from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from . import models, schemas
from .database import get_db, engine, Base
from .matcher import find_matches

Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/lost-found", tags=["Lost & Found"])


@router.post("/report-lost", response_model=schemas.ItemOut)
def report_lost(payload: schemas.ItemCreate, db: Session = Depends(get_db)):
    item = models.Item(type="lost", status="open", **payload.dict())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.post("/report-found", response_model=schemas.ItemOut)
def report_found(payload: schemas.ItemCreate, db: Session = Depends(get_db)):
    item = models.Item(type="found", status="open", **payload.dict())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/items", response_model=list[schemas.ItemOut])
def list_items(type: str | None = None, status: str | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Item)
    if type:
        q = q.filter(models.Item.type == type)
    if status:
        q = q.filter(models.Item.status == status)
    return q.order_by(models.Item.created_at.desc()).all()


@router.get("/item/{item_id}", response_model=schemas.ItemOut)
def get_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(404, "Item not found")
    return item


@router.get("/matches/{item_id}", response_model=list[schemas.MatchOut])
def get_matches(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(404, "Item not found")

    opposite = "found" if item.type == "lost" else "lost"
    candidates = db.query(models.Item).filter(
        and_(models.Item.type == opposite, models.Item.status == "open")
    ).all()

    matches = find_matches(item, candidates)
    return [{"item": m[0], "score": round(m[1], 3)} for m in matches]


@router.post("/resolve/{item_id}")
def resolve_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        raise HTTPException(404, "Item not found")
    item.status = "resolved"
    db.commit()
    return {"status": "resolved", "id": item_id}
