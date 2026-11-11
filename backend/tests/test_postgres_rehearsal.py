"""Actual PostgreSQL acceptance; requires explicit disposable PostgreSQL 16 DSN."""
import hashlib
import json
import os

import pytest

from evaluation.governed_answers.postgres_rehearsal import run_rehearsal


def test_postgres_requires_explicit_dsn_before_io(tmp_path):
    with pytest.raises(ValueError):
        run_rehearsal(None,tmp_path / "absent.json")
    assert not (tmp_path / "absent.json").exists()


def test_postgres_refuses_backup_overwrite_before_connect(tmp_path):
    artifact = tmp_path / "backup.json"
    artifact.write_text("preserved")
    with pytest.raises(FileExistsError):
        run_rehearsal("not a DSN",artifact)
    assert artifact.read_text() == "preserved"


def test_actual_postgres_transactions_and_exact_artifact_restore(tmp_path):
    dsn = os.environ.get("SENTINEL_ISOLATED_POSTGRES_DSN")
    if not dsn:
        pytest.skip("explicit isolated PostgreSQL 16 DSN required")
    artifact = tmp_path / "backup.json"
    report = run_rehearsal(dsn,artifact)
    assert all(report["checks"].values())
    assert report["source_inventory_sha256"] == report["restore_inventory_sha256"]
    assert report["backup_sha256"] == hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert report["counts"] == {"principals":1,"scopes":1,"grants":0,"identities":1,"versions":1,"chunks":2,"outbox":4}
    assert report["index_verified"] is report["application_migrated"] is report["production_enabled"] is report["release_authorized"] is False
    assert report["database"] == "sentinel_sprint21_rehearsal"
    backup = json.loads(artifact.read_text())
    assert backup["tables"]["identities"]["rows"][0][-1] == "tombstoned"
    assert backup["tables"]["principals"]["rows"][0][1] == 2
