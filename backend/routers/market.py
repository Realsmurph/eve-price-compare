from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..clients.esi import ESIClientError
from ..database import get_db
from ..schemas import EveTypeRead, MarketComparisonRead
from ..services.item_search_service import ItemSearchService
from ..services.market_service import MarketService


router = APIRouter(prefix="/api/items", tags=["market"])


def get_market_service() -> MarketService:
    return MarketService()


def get_item_search_service(db: Session = Depends(get_db)) -> ItemSearchService:
    return ItemSearchService(db)


@router.get("/search", response_model=list[EveTypeRead])
def search_items(
    q: str = Query(min_length=1, max_length=100),
    limit: int = Query(default=25, ge=1, le=100),
    sort: str = Query(default="name", pattern="^(name|type_id|market_group)$"),
    published: bool = Query(default=True),
    market_only: bool = Query(default=True),
    service: ItemSearchService = Depends(get_item_search_service),
):
    return service.search(
        q,
        limit=limit,
        sort=sort,
        published=published,
        market_only=market_only,
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
