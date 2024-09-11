"""Add tram number to Invoice

Revision ID: a2f3037a7ee3
Revises: 8c2e71ed161e
Create Date: 2024-09-10 18:36:28.846960

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a2f3037a7ee3'
down_revision = '8c2e71ed161e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('invoices', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tram_num', sa.String(length=10), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('invoices', schema=None) as batch_op:
        batch_op.drop_column('tram_num')

    # ### end Alembic commands ###
