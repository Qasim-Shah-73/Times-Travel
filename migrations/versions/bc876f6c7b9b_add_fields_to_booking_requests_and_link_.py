from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'bc876f6c7b9b'
down_revision = '5fc4e98a5680'
branch_labels = None
depends_on = None


def upgrade():
    # Drop 'room_request' table if it already exists
    conn = op.get_bind()

    conn.execute(text("DROP TABLE IF EXISTS room_request"))
    conn.execute(text("DROP TABLE IF EXISTS _alembic_tmp_booking_request"))


    # Create 'room_request' table
    op.create_table('room_request',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('booking_request_id', sa.Integer(), nullable=False),
        sa.Column('room_type', sa.String(length=100), nullable=False),
        sa.Column('inclusion', sa.String(length=100), nullable=False),
        sa.Column('price_to_beat', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['booking_request_id'], ['booking_request.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add new columns to the 'booking_request' table
    with op.batch_alter_table('booking_request', schema=None) as batch_op:
        # Add columns with default values to avoid conflicts with existing rows
        batch_op.add_column(sa.Column('destination', sa.String(length=128), nullable=False, server_default='Unknown'))
        batch_op.add_column(sa.Column('num_rooms', sa.Integer(), nullable=False, server_default='1'))
        batch_op.drop_column('room_type')

    # Remove the server defaults after existing rows have been populated
    with op.batch_alter_table('booking_request', schema=None) as batch_op:
        batch_op.alter_column('destination', server_default=None)
        batch_op.alter_column('num_rooms', server_default=None)

    # Link 'bookings' with 'booking_request'
    with op.batch_alter_table('bookings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('booking_request_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('tmp_booking_request', 'booking_request', ['booking_request_id'], ['id'])


def downgrade():
    # Drop foreign key and column from 'bookings'
    with op.batch_alter_table('bookings', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('booking_request_id')

    # Revert changes in 'booking_request' table
    with op.batch_alter_table('booking_request', schema=None) as batch_op:
        batch_op.add_column(sa.Column('room_type', sa.VARCHAR(length=128), nullable=False))
        batch_op.drop_column('num_rooms')
        batch_op.drop_column('destination')

    # Drop the 'room_request' table
    op.drop_table('room_request')
