"""Create the document catalog omitted by the original empty revision.

Revision ID: 031_document_catalog
Revises: 01620884d63e
"""
from alembic import op
import sqlalchemy as sa

revision = '031_document_catalog'
down_revision = '01620884d63e'
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table('documents'):
        required = {'id', 'filename', 'file_hash', 'module', 'topic', 'collection',
                    'description', 'chunk_count', 'embedding_model', 'status',
                    'organization_id', 'uploaded_at'}
        actual = {c['name'] for c in inspector.get_columns('documents')}
        if not required <= actual:
            raise RuntimeError('Existing documents schema is incompatible; back up and migrate its missing columns explicitly.')
        return
    op.create_table(
        'documents',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('file_hash', sa.String(), nullable=False),
        sa.Column('module', sa.String(), server_default='engineering'),
        sa.Column('topic', sa.String(), server_default='general'),
        sa.Column('collection', sa.String(), server_default='general'),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('chunk_count', sa.Integer(), server_default='0'),
        sa.Column('embedding_model', sa.String(), nullable=False),
        sa.Column('status', sa.String(), server_default='indexed'),
        sa.Column('organization_id', sa.String(), server_default='default'),
        sa.Column('uploaded_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_documents_id', 'documents', ['id'])
    op.create_index('ix_documents_file_hash', 'documents', ['file_hash'], unique=True)


def downgrade():
    op.drop_index('ix_documents_file_hash', table_name='documents')
    op.drop_index('ix_documents_id', table_name='documents')
    op.drop_table('documents')
