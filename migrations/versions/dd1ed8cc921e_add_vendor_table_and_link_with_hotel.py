"""Add Vendor table and link with Hotel

Revision ID: dd1ed8cc921e
Revises: f9d3b0c174fc
Create Date: 2024-09-05 12:24:34.238729

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dd1ed8cc921e'
down_revision = 'f9d3b0c174fc'
branch_labels = None
depends_on = None

def upgrade():
    # Create the 'vendors' table
    op.create_table(
        'vendors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('contact_person', sa.String(length=100), nullable=False),
        sa.Column('phone_number', sa.BigInteger(), nullable=True),
        sa.Column('bank_details', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # Add 'vendor_id' column to 'hotel' table and create a foreign key constraint
    with op.batch_alter_table('hotel', schema=None) as batch_op:
        batch_op.add_column(sa.Column('vendor_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_hotel_vendor',  # Name of the foreign key constraint
            'vendors',          # Referenced table
            ['vendor_id'],      # Local column
            ['id']              # Referenced column
        )

def downgrade():
    # Remove foreign key constraint and 'vendor_id' column from 'hotel' table
    with op.batch_alter_table('hotel', schema=None) as batch_op:
        batch_op.drop_constraint('fk_hotel_vendor', type_='foreignkey')
        batch_op.drop_column('vendor_id')

    # Drop the 'vendors' table
    op.drop_table('vendors')