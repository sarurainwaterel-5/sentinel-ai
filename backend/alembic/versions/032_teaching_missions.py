"""Persistent local teaching missions, additive to existing knowledge."""
from alembic import op
import sqlalchemy as sa

revision = "032_teaching_missions"
down_revision = "031_document_catalog"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table("teaching_missions"):
        required = {"id", "organization_id", "domain_id", "filename", "file_path", "topic", "description", "status", "stage", "created_at", "updated_at", "events", "result", "error"}
        actual = {column["name"] for column in inspector.get_columns("teaching_missions")}
        if not required <= actual:
            raise RuntimeError("Existing teaching mission schema is incompatible; preserve it and migrate explicitly.")
        indexes = {index["name"] for index in inspector.get_indexes("teaching_missions")}
        if "ix_teaching_missions_organization_id" not in indexes:
            op.create_index("ix_teaching_missions_organization_id", "teaching_missions", ["organization_id"])
        return
    op.create_table("teaching_missions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("organization_id", sa.String(), nullable=False),
        sa.Column("domain_id", sa.String(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("file_path", sa.String(), nullable=False),
        sa.Column("topic", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("stage", sa.String(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.Column("updated_at", sa.String(), nullable=False),
        sa.Column("events", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error", sa.String(), nullable=True))
    op.create_index("ix_teaching_missions_organization_id", "teaching_missions", ["organization_id"])


def downgrade():
    op.drop_table("teaching_missions")
