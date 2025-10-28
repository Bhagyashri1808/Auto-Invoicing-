"""Extend extracted_data table with LLM fields

Revision ID: 003_extend_extracted_data
Revises: 002_enhanced_processing
Create Date: 2025-01-23 12:01:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003_extend_extracted_data'
down_revision = '002_enhanced_processing'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to existing extracted_data table
    op.add_column('extracted_data', sa.Column('extraction_method', sa.String(50), nullable=False, server_default='OCR_ONLY'))
    op.add_column('extracted_data', sa.Column('llm_processing_job_id', sa.String(36), nullable=True))
    op.add_column('extracted_data', sa.Column('ocr_confidence_avg', sa.Float(), nullable=True))
    op.add_column('extracted_data', sa.Column('llm_confidence_score', sa.Float(), nullable=True))
    op.add_column('extracted_data', sa.Column('field_confidence_scores', sa.JSON(), nullable=True))
    op.add_column('extracted_data', sa.Column('preprocessing_applied', sa.Boolean(), nullable=False, server_default='0'))
    op.add_column('extracted_data', sa.Column('preprocessing_method', sa.String(255), nullable=True))
    op.add_column('extracted_data', sa.Column('validation_errors', sa.JSON(), nullable=True))
    op.add_column('extracted_data', sa.Column('has_manual_corrections', sa.Boolean(), nullable=False, server_default='0'))

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_extracted_data_llm_job',
        'extracted_data', 'llm_processing_jobs',
        ['llm_processing_job_id'], ['id']
    )

    # Add index for extraction method
    op.create_index('idx_extracted_data_method', 'extracted_data', ['extraction_method'])


def downgrade() -> None:
    # Drop index
    op.drop_index('idx_extracted_data_method', table_name='extracted_data')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_extracted_data_llm_job', 'extracted_data', type_='foreignkey')
    
    # Drop columns
    op.drop_column('extracted_data', 'has_manual_corrections')
    op.drop_column('extracted_data', 'validation_errors')
    op.drop_column('extracted_data', 'preprocessing_method')
    op.drop_column('extracted_data', 'preprocessing_applied')
    op.drop_column('extracted_data', 'field_confidence_scores')
    op.drop_column('extracted_data', 'llm_confidence_score')
    op.drop_column('extracted_data', 'ocr_confidence_avg')
    op.drop_column('extracted_data', 'llm_processing_job_id')
    op.drop_column('extracted_data', 'extraction_method')