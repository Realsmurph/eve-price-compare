from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..clients.esi import ESIClientError
from ..database import get_db
from ..schemas import EveTypeRead, MarketComparisonRead, MarketPriceHistoryRead
from ..services.item_search_service import ItemSearchService
from ..services.market_service import MarketService
from ..services.price_history_service import PriceHistoryService


router = APIRouter(prefix="/api/items", tags=["market"])


def get_market_service(db: Session = Depends(get_db)) -> MarketService:
    return MarketService(db)


def get_item_search_service(db: Session = Depends(get_db)) -> ItemSearchService:
    return ItemSearchService(db)


@router.get("/search", response_model=list[EveTypeRead])
def search_items(
    q: str = Query(min_length=1, max_length=100),
    limit: int = Query(default=25, ge=1, le=100),
    sort: str = Query(default="name", pattern="^(name|type_id|market_group|category)$"),
    published: bool = Query(default=True),
    market_only: bool = Query(default=True),
    category: str | None = Query(default=None, max_length=100),
    group: str | None = Query(default=None, max_length=100),
    service: ItemSearchService = Depends(get_item_search_service),
):
    return service.search(
        q,
        limit=limit,
        sort=sort,
        published=published,
        market_only=market_only,
        category=category,
        group=group,
    )


@router.get("/compare", response_model=MarketComparisonRead)
async def compare_item_markets(
    type_id: int = Query(gt=0),
    service: MarketService = Depends(get_market_service),
):
    try:
        return await service.compare_item(type_id)
    except ESIClientError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


@router.get("/{type_id}/history", response_model=list[MarketPriceHistoryRead])
def item_price_history(
    type_id: int,
    hub: str | None = Query(default=None, max_length=32),
    limit: int = Query(default=90, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    return PriceHistoryService(db).list_history(type_id=type_id, hub=hub, limit=limit)
