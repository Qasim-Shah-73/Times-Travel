"""Remove is_agency_admin and is_admin columns from User model

Revision ID: 9a081586ac1d
Revises: 453fa01c2885
Create Date: 2024-09-04 13:36:46.449385

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a081586ac1d'
down_revision = '453fa01c2885'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('is_admin')
        batch_op.drop_column('is_agency_admin')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_agency_admin', sa.BOOLEAN(), nullable=True))
        batch_op.add_column(sa.Column('is_admin', sa.BOOLEAN(), nullable=True))

    # ### end Alembic commands ###
