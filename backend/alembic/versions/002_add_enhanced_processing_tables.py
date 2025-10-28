"""Add enhanced processing tables

Revision ID: 002_enhanced_processing
Revises: 
Create Date: 2025-01-23 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '002_enhanced_processing'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create preprocessing_configurations table
    op.create_table(
        'preprocessing_configurations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(255), nullable=False, default='default'),
        sa.Column('operation_type', sa.String(50), nullable=False),
        sa.Column('target_width', sa.Integer(), nullable=False, default=1600),
        sa.Column('threshold_block_size', sa.Integer(), nullable=False, default=11),
        sa.Column('threshold_constant', sa.Float(), nullable=False, default=10.0),
        sa.Column('bilateral_filter_d', sa.Integer(), nullable=False, default=9),
        sa.Column('bilateral_sigma_color', sa.Float(), nullable=False, default=75.0),
        sa.Column('bilateral_sigma_space', sa.Float(), nullable=False, default=75.0),
        sa.Column('is_default', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()),
        sa.CheckConstraint('threshold_block_size % 2 = 1', name='valid_threshold_block_size'),
        sa.CheckConstraint('target_width BETWEEN 800 AND 3200', name='valid_target_width'),
        sa.CheckConstraint("operation_type IN ('THRESHOLD', 'DESKEW', 'COMBINED')", name='valid_operation_type')
    )

    # Create llm_processing_jobs table
    op.create_table(
        'llm_processing_jobs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('invoice_document_id', sa.String(36), nullable=False),
        sa.Column('preprocessing_config_id', sa.String(36), nullable=True),
        sa.Column('llm_model_name', sa.String(255), nullable=False),
        sa.Column('preprocessed_image_path', sa.Text(), nullable=True),
        sa.Column('llm_request_payload', sa.JSON(), nullable=True),
        sa.Column('llm_response_raw', sa.JSON(), nullable=True),
        sa.Column('llm_response_validated', sa.JSON(), nullable=True),
        sa.Column('processing_started_at', sa.DateTime(), nullable=False),
        sa.Column('llm_started_at', sa.DateTime(), nullable=True),
        sa.Column('llm_completed_at', sa.DateTime(), nullable=True),
        sa.Column('processing_completed_at', sa.DateTime(), nullable=True),
        sa.Column('timeout_occurred', sa.Boolean(), nullable=False, default=False),
        sa.Column('fallback_triggered', sa.Boolean(), nullable=False, default=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
        sa.Column('max_retries', sa.Integer(), nullable=False, default=3),
        sa.Column('memory_peak_mb', sa.Integer(), nullable=True),
        sa.Column('processing_duration_ms', sa.Integer(), nullable=True),
        sa.CheckConstraint('retry_count <= max_retries', name='valid_retry_count'),
        sa.ForeignKeyConstraint(['preprocessing_config_id'], ['preprocessing_configurations.id'], name='fk_llm_jobs_preprocessing_config')
    )

    # Create processing_performance_metrics table
    op.create_table(
        'processing_performance_metrics',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('invoice_document_id', sa.String(36), nullable=False),
        sa.Column('processing_date', sa.Date(), nullable=False),
        sa.Column('extraction_method', sa.String(50), nullable=False),
        sa.Column('preprocessing_duration_ms', sa.Integer(), nullable=True),
        sa.Column('ocr_duration_ms', sa.Integer(), nullable=True),
        sa.Column('llm_duration_ms', sa.Integer(), nullable=True),
        sa.Column('total_duration_ms', sa.Integer(), nullable=False),
        sa.Column('memory_peak_mb', sa.Float(), nullable=False),
        sa.Column('file_size_mb', sa.Float(), nullable=False),
        sa.Column('image_dimensions', sa.String(50), nullable=True),
        sa.Column('preprocessing_applied', sa.Boolean(), nullable=False),
        sa.Column('timeout_occurred', sa.Boolean(), nullable=False),
        sa.Column('error_occurred', sa.Boolean(), nullable=False),
        sa.Column('accuracy_score', sa.Float(), nullable=True),
        sa.Column('user_corrections_count', sa.Integer(), nullable=False, default=0),
        sa.CheckConstraint('accuracy_score IS NULL OR (accuracy_score BETWEEN 0.0 AND 1.0)', name='valid_accuracy_score'),
        sa.CheckConstraint("extraction_method IN ('OCR_ONLY', 'LLM_PRIMARY', 'LLM_FALLBACK')", name='valid_extraction_method')
    )

    # Create indexes for performance optimization
    op.create_index('idx_llm_jobs_invoice_id', 'llm_processing_jobs', ['invoice_document_id'])
    op.create_index('idx_llm_jobs_status', 'llm_processing_jobs', ['processing_completed_at', 'timeout_occurred'])
    op.create_index('idx_preprocessing_configs_default', 'preprocessing_configurations', ['is_default'], unique=False, sqlite_where=sa.text('is_default = 1'))
    op.create_index('idx_performance_metrics_date', 'processing_performance_metrics', ['processing_date'])
    op.create_index('idx_performance_metrics_method', 'processing_performance_metrics', ['extraction_method'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_performance_metrics_method', table_name='processing_performance_metrics')
    op.drop_index('idx_performance_metrics_date', table_name='processing_performance_metrics')
    op.drop_index('idx_preprocessing_configs_default', table_name='preprocessing_configurations')
    op.drop_index('idx_llm_jobs_status', table_name='llm_processing_jobs')
    op.drop_index('idx_llm_jobs_invoice_id', table_name='llm_processing_jobs')
    
    # Drop tables
    op.drop_table('processing_performance_metrics')
    op.drop_table('llm_processing_jobs')
    op.drop_table('preprocessing_configurations')