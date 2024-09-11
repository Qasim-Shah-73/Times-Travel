"""Add room_id foreign key to Booking and establish relationships

Revision ID: b34ae5022ab4
Revises: a2f3037a7ee3
Create Date: 2024-09-11 14:35:39.853323

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b34ae5022ab4'
down_revision = 'a2f3037a7ee3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('bookings', schema=None) as batch_op:
        # Add the new column
        batch_op.add_column(sa.Column('room_id', sa.Integer(), nullable=True))
        
        # Create the foreign key constraint with a name
        batch_op.create_foreign_key(
            'fk_room_id',  # Name of the foreign key constraint
            'room',        # Referenced table
            ['room_id'],   # Columns in this table
            ['id']         # Columns in the referenced table
        )
        
        # Optionally drop the old column
        batch_op.drop_column('room_type')



def downgrade():
    with op.batch_alter_table('bookings', schema=None) as batch_op:
        # Re-add the old column if necessary
        batch_op.add_column(sa.Column('room_type', sa.String(length=128), nullable=True))
        
        # Drop the foreign key constraint by name
        batch_op.drop_constraint('fk_room_id', 'bookings', type_='foreignkey')
        
        # Drop the new column
        batch_op.drop_column('room_id')
