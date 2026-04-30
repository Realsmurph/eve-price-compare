from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import WatchlistItem
from ..schemas import WatchlistItemCreate, WatchlistItemUpdate


class WatchlistService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, payload: WatchlistItemCreate) -> WatchlistItem:
        item = WatchlistItem(**payload.model_dump())
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def list(self) -> list[WatchlistItem]:
        statement = select(WatchlistItem).order_by(WatchlistItem.created_at.desc())
        return list(self.db.scalars(statement))

    def get(self, item_id: int) -> WatchlistItem | None:
        return self.db.get(WatchlistItem, item_id)

    def update(
        self,
        item_id: int,
        payload: WatchlistItemUpdate,
    ) -> WatchlistItem | None:
        item = self.get(item_id)
        if item is None:
            return None

        updates = payload.model_dump(exclude_unset=True)
        for key, value in updates.items():
            setattr(item, key, value)

        self.db.commit()
        self.db.refresh(item)
        return item

    def delete(self, item_id: int) -> bool:
        item = self.get(item_id)
        if item is None:
            return False

        self.db.delete(item)
        self.db.commit()
        return True
