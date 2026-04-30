from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import WatchlistItemCreate, WatchlistItemRead, WatchlistItemUpdate
from ..services.watchlist_service import WatchlistService


router = APIRouter(prefix="/watchlist", tags=["watchlist"])


def get_watchlist_service(db: Session = Depends(get_db)) -> WatchlistService:
    return WatchlistService(db)


@router.post(
    "",
    response_model=WatchlistItemRead,
    status_code=status.HTTP_201_CREATED,
)
def create_watchlist_item(
    payload: WatchlistItemCreate,
    service: WatchlistService = Depends(get_watchlist_service),
):
    return service.create(payload)


@router.get("", response_model=list[WatchlistItemRead])
def list_watchlist_items(
    service: WatchlistService = Depends(get_watchlist_service),
):
    return service.list()


@router.get("/{item_id}", response_model=WatchlistItemRead)
def get_watchlist_item(
    item_id: int,
    service: WatchlistService = Depends(get_watchlist_service),
):
    item = service.get(item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@router.put("/{item_id}", response_model=WatchlistItemRead)
def update_watchlist_item(
    item_id: int,
    payload: WatchlistItemUpdate,
    service: WatchlistService = Depends(get_watchlist_service),
):
    item = service.update(item_id, payload)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_watchlist_item(
    item_id: int,
    service: WatchlistService = Depends(get_watchlist_service),
):
    deleted = service.delete(item_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
