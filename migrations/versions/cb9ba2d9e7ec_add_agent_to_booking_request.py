"""Add agent to Booking request

Revision ID: cb9ba2d9e7ec
Revises: 9c3807e3fea3
Create Date: 2024-09-30 18:22:54.649022

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cb9ba2d9e7ec'
down_revision = '9c3807e3fea3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('booking_request', schema=None) as batch_op:
        batch_op.add_column(sa.Column('agent_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_booking_request_agent_id', 'users', ['agent_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('booking_request', schema=None) as batch_op:
        batch_op.drop_constraint('fk_booking_request_agent_id', type_='foreignkey')
        batch_op.drop_column('agent_id')

    # ### end Alembic commands ###
