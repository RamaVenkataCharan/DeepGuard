"""
Alembic Migration: Update Customer Schema for Electricity Theft System
Revision ID: 002_update_customer_schema
Revises: 001_initial_schema
Create Date: 2026-07-30

Description:
Replaces legacy customer fields with smart meter utility account attributes:
- meter_id (SGCC CONS_NO link)
- tariff_category
- feeder_line
- region_code
- sanctioned_load_kw
- connection_type (Enum: Residential, Commercial, Industrial)

Data Migration:
- Converts existing lowercase connection_type values ('residential', 'commercial', 'industrial')
  to capitalized casing ('Residential', 'Commercial', 'Industrial') during upgrade().
- Generates default meter_id values ('MTR-SGCC-XXXX') for existing records before setting NOT NULL.
- Downgrade path converts connection_type back to lowercase and safely drops added columns.
"""

from alembic import op
import sqlalchemy as sa

# Revision identifiers
revision = '002_update_customer_schema'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add smart meter utility columns
    op.add_column('customers', sa.Column('meter_id', sa.String(length=64), nullable=True))
    op.add_column('customers', sa.Column('region_code', sa.String(length=50), nullable=True))
    op.add_column('customers', sa.Column('feeder_line', sa.String(length=100), nullable=True))
    op.add_column('customers', sa.Column('tariff_category', sa.String(length=100), nullable=False, server_default='LT-Residential'))
    op.add_column('customers', sa.Column('sanctioned_load_kw', sa.Float(), nullable=True))

    # 2. Data Migration: Populate default meter_id for existing rows before NOT NULL & UNIQUE constraints
    op.execute("UPDATE customers SET meter_id = 'MTR-SGCC-' || printf('%04d', id) WHERE meter_id IS NULL OR meter_id = ''")
    op.alter_column('customers', 'meter_id', nullable=False)

    # 3. Data Migration: Convert existing lowercase connection_type to Capitalized casing
    op.execute("UPDATE customers SET connection_type = 'Residential' WHERE LOWER(connection_type) = 'residential'")
    op.execute("UPDATE customers SET connection_type = 'Commercial' WHERE LOWER(connection_type) = 'commercial'")
    op.execute("UPDATE customers SET connection_type = 'Industrial' WHERE LOWER(connection_type) = 'industrial'")

    # 4. Indexes & Unique constraints
    op.create_index(op.f('ix_customers_meter_id'), 'customers', ['meter_id'], unique=True)
    op.create_index(op.f('ix_customers_region_code'), 'customers', ['region_code'], unique=False)
    op.create_index(op.f('ix_customers_feeder_line'), 'customers', ['feeder_line'], unique=False)

    # 5. Safely drop legacy agricultural columns if physically present
    with op.batch_alter_table('customers') as batch_op:
        for legacy_col in ['location', 'acreage', 'crop_type']:
            try:
                batch_op.drop_column(legacy_col)
            except Exception:
                pass


def downgrade():
    # 1. Data Migration: Revert connection_type values to lowercase
    op.execute("UPDATE customers SET connection_type = 'residential' WHERE connection_type = 'Residential'")
    op.execute("UPDATE customers SET connection_type = 'commercial' WHERE connection_type = 'Commercial'")
    op.execute("UPDATE customers SET connection_type = 'industrial' WHERE connection_type = 'Industrial'")

    # 2. Re-add historical agricultural columns for data-safe rollback
    op.add_column('customers', sa.Column('location', sa.String(length=255), nullable=True))
    op.add_column('customers', sa.Column('acreage', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('customers', sa.Column('crop_type', sa.String(length=100), nullable=True, server_default='N/A'))

    # 3. Drop smart meter index & columns
    op.drop_index(op.f('ix_customers_feeder_line'), table_name='customers')
    op.drop_index(op.f('ix_customers_region_code'), table_name='customers')
    op.drop_index(op.f('ix_customers_meter_id'), table_name='customers')

    with op.batch_alter_table('customers') as batch_op:
        batch_op.drop_column('sanctioned_load_kw')
        batch_op.drop_column('tariff_category')
        batch_op.drop_column('feeder_line')
        batch_op.drop_column('region_code')
        batch_op.drop_column('meter_id')
