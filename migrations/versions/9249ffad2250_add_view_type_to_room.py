"""Add View type to Room

Revision ID: 9249ffad2250
Revises: 14eda469beec
Create Date: 2024-09-30 12:00:26.998307

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9249ffad2250'
down_revision = '14eda469beec'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('room', schema=None) as batch_op:
        batch_op.add_column(sa.Column('view_type', sa.String(length=100), nullable=False, server_default='Standard'))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('room', schema=None) as batch_op:
        batch_op.drop_column('view_type')

    # ### end Alembic commands ###
