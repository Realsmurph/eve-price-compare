import argparse

from ..services.static_data_loader import StaticDataLoader


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh EVE static data from Fuzzwork SDE CSV files.")
    parser.add_argument("--force", action="store_true", help="Update existing types and reload reactions.")
    args = parser.parse_args()

    count = StaticDataLoader().load(force=args.force)
    print(f"Loaded or refreshed {count} static data rows.")


if __name__ == "__main__":
    main()
