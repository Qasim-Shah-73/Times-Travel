"""Add Vendor table and link with Hotel

Revision ID: 6a843d527f3e
Revises: f9d3b0c174fc
Create Date: 2024-09-04 19:22:48.205268

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6a843d527f3e'
down_revision = 'f9d3b0c174fc'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('vendors',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('contact_person', sa.String(length=100), nullable=False),
    sa.Column('phone_number', sa.BigInteger(), nullable=True),
    sa.Column('bank_details', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    with op.batch_alter_table('hotel', schema=None) as batch_op:
        batch_op.add_column(sa.Column('vendor_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'vendors', ['vendor_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('hotel', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('vendor_id')

    op.drop_table('vendors')
    # ### end Alembic commands ###
