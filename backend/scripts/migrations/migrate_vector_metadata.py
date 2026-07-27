"""
Run SentinelAI's vector metadata migration.

Examples:

Dry run:
    python -m scripts.migrations.migrate_vector_metadata

Apply migration:
    python -m scripts.migrations.migrate_vector_metadata --apply
"""

import argparse
import json

from app.database import SessionLocal
from app.services.migrations.vector_metadata_migration import (
    VectorMetadataMigration,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the migration instead of running a dry run.",
    )

    args = parser.parse_args()

    db = SessionLocal()

    try:
        migration = VectorMetadataMigration(db)

        report = migration.run(
            dry_run=not args.apply,
        )

        print(json.dumps(report, indent=2))

    finally:
        db.close()


if __name__ == "__main__":
    main()
