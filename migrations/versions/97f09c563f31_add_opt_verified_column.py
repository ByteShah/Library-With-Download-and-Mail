"""Add opt verified column

Revision ID: 97f09c563f31
Revises: 8d1a38947f34
Create Date: 2024-07-20 14:51:21.721442

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '97f09c563f31'
down_revision = '8d1a38947f34'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('otp', schema=None) as batch_op:
        batch_op.add_column(sa.Column('email_verified', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('otp', schema=None) as batch_op:
        batch_op.drop_column('email_verified')

    # ### end Alembic commands ###
