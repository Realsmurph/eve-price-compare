from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import ReactionProfitRead
from ..services.reaction_service import (
    MissingPriceError,
    ReactionNotFoundError,
    ReactionService,
)


router = APIRouter(prefix="/api/reactions", tags=["reactions"])


def get_reaction_service(db: Session = Depends(get_db)) -> ReactionService:
    return ReactionService(db)


@router.get("/{type_id}", response_model=ReactionProfitRead)
def get_reaction_profit(
    type_id: int,
    import_rate: Decimal = Query(default=Decimal("0"), ge=0),
    import_flat_fee: Decimal = Query(default=Decimal("0"), ge=0),
    service: ReactionService = Depends(get_reaction_service),
):
    try:
        return service.calculate_profit(
            type_id,
            import_rate=import_rate,
            import_flat_fee=import_flat_fee,
        )
    except ReactionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except MissingPriceError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
