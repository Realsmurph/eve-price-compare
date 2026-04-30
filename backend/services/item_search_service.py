from sqlalchemy import case, select
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
        category: str | None = None,
        group: str | None = None,
    ) -> list[EveType]:
        normalized_query = query.strip()
        if not normalized_query:
            return []

        prefix_rank = case((EveType.name.ilike(f"{normalized_query}%"), 0), else_=1)
        statement = select(EveType).where(EveType.name.ilike(f"%{normalized_query}%"))
        if published:
            statement = statement.where(EveType.published.is_(True))
        if market_only:
            statement = statement.where(EveType.market_group_id.is_not(None))
        if category:
            statement = statement.where(EveType.category_name.ilike(category.strip()))
        if group:
            statement = statement.where(EveType.group_name.ilike(group.strip()))

        if sort == "type_id":
            statement = statement.order_by(EveType.type_id.asc())
        elif sort == "market_group":
            statement = statement.order_by(
                EveType.market_group_id.asc().nulls_last(),
                EveType.name.asc(),
            )
        elif sort == "category":
            statement = statement.order_by(
                EveType.category_name.asc().nulls_last(),
                EveType.group_name.asc().nulls_last(),
                prefix_rank.asc(),
                EveType.name.asc(),
            )
        else:
            statement = statement.order_by(prefix_rank.asc(), EveType.name.asc())

        statement = statement.limit(limit)
        return list(self.db.scalars(statement))
