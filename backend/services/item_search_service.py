from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import EveType


class ItemSearchService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def search(
        self,
        query: str,
        limit: int = 25,
        sort: str = "name",
        published: bool = True,
        market_only: bool = True,
    ) -> list[EveType]:
        normalized_query = query.strip()
        if not normalized_query:
            return []

        statement = select(EveType).where(EveType.name.ilike(f"%{normalized_query}%"))
        if published:
            statement = statement.where(EveType.published.is_(True))
        if market_only:
            statement = statement.where(EveType.market_group_id.is_not(None))

        if sort == "type_id":
            statement = statement.order_by(EveType.type_id.asc())
        elif sort == "market_group":
            statement = statement.order_by(
                EveType.market_group_id.asc().nulls_last(),
                EveType.name.asc(),
            )
        else:
            statement = statement.order_by(EveType.name.asc())

        statement = statement.limit(limit)
        return list(self.db.scalars(statement))
