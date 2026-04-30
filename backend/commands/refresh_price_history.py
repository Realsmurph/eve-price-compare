import argparse
import asyncio

from ..database import SessionLocal
from ..services.price_refresh_service import PriceRefreshService


async def _run(limit: int, all_items: bool, daily: bool) -> int:
    with SessionLocal() as db:
        service = PriceRefreshService(db)
        if daily:
            return await service.refresh_daily_history(limit=limit, all_items=all_items)
        return await service.refresh_snapshots(limit=limit, all_items=all_items)


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh market price history.")
    parser.add_argument("--limit", type=int, default=250, help="Maximum items to refresh.")
    parser.add_argument("--all-items", action="store_true", help="Use all marketable static types.")
    parser.add_argument(
        "--daily",
        action="store_true",
        help="Load ESI daily market history instead of current order snapshots.",
    )
    args = parser.parse_args()

    count = asyncio.run(_run(limit=args.limit, all_items=args.all_items, daily=args.daily))
    noun = "history rows" if args.daily else "item snapshots"
    print(f"Refreshed {count} {noun}.")


if __name__ == "__main__":
    main()
