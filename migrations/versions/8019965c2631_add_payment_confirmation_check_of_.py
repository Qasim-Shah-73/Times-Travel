"""Add payment confirmation check of vendor on a booking

Revision ID: 8019965c2631
Revises: fab9ed0940df
Create Date: 2024-09-27 17:16:26.904785

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8019965c2631'
down_revision = 'fab9ed0940df'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('bookings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('vendor_paid', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('bookings', schema=None) as batch_op:
        batch_op.drop_column('vendor_paid')

    # ### end Alembic commands ###
