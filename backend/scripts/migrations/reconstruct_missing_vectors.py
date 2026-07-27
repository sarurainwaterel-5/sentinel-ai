"""
Reconstruct missing SentinelAI vector memory.

Dry run:

    python -m scripts.migrations.reconstruct_missing_vectors \
      Kubernetes_up_running.pdf \
      postgresql-19-US.pdf \
      Introduction-to-Docker.pdf

Apply:

    python -m scripts.migrations.reconstruct_missing_vectors \
      --apply \
      Kubernetes_up_running.pdf \
      postgresql-19-US.pdf \
      Introduction-to-Docker.pdf
"""

import argparse
import json

from app.database import SessionLocal
from app.services.migrations.vector_reconstruction import (
    VectorReconstructionService,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Reconstruct missing Qdrant vectors from existing PDFs."
        )
    )

    parser.add_argument(
        "filenames",
        nargs="*",
        help="Exact stored filenames to reconstruct.",
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write reconstructed vectors to Qdrant.",
    )

    return parser.parse_args()


def print_report(report: dict) -> None:
    print()
    print("=" * 60)
    print("SentinelAI — Vector Memory Reconstruction")
    print("=" * 60)
    print()

    print(
        "Mode                         :",
        "APPLY" if not report["dry_run"] else "DRY RUN",
    )
    print(
        "Documents scanned            :",
        report["documents_scanned"],
    )
    print(
        "Documents requiring rebuild  :",
        report["documents_requiring_reconstruction"],
    )
    print(
        "Documents reconstructed      :",
        report["documents_reconstructed"],
    )
    print(
        "Documents already present    :",
        report["documents_already_present"],
    )
    print(
        "Source files missing         :",
        report["source_files_missing"],
    )
    print(
        "Documents without text       :",
        report["documents_without_text"],
    )
    print(
        "Vectors reconstructed        :",
        report["vectors_reconstructed"],
    )
    print(
        "Failures                     :",
        len(report["failures"]),
    )

    print()
    print("-" * 60)
    print("Memory Status:", report["memory_status"])
    print("-" * 60)

    print()
    print("Results:")
    print(json.dumps(report["results"], indent=2))

    if report["failures"]:
        print()
        print("Failures:")
        print(json.dumps(report["failures"], indent=2))

    print()
    print("=" * 60)


def main() -> None:
    arguments = parse_arguments()
    db = SessionLocal()

    try:
        service = VectorReconstructionService(db)

        report = service.run(
            filenames=arguments.filenames or None,
            dry_run=not arguments.apply,
        )

        print_report(report)
    finally:
        db.close()


if __name__ == "__main__":
    main()
