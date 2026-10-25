import argparse
import asyncio
import json

from app.db.session import AsyncSessionLocal, engine
from app.services.wikimedia_import import LANGUAGE_WIKIS, import_random_wikipedia_pages


async def main() -> None:
    parser = argparse.ArgumentParser(description="Import a small, rights-labelled Wikimedia Wikipedia sample.")
    parser.add_argument("--language", choices=sorted(LANGUAGE_WIKIS), default="ki")
    parser.add_argument("--pages", type=int, default=10, help="Number of random pages to request (1–50).")
    args = parser.parse_args()

    async with AsyncSessionLocal() as db:
        try:
            result = await import_random_wikipedia_pages(db, args.language, args.pages)
            await db.commit()
            print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        except Exception:
            await db.rollback()
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
