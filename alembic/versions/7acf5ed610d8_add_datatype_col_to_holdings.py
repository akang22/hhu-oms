"""Add datatype col to holdings

Revision ID: 7acf5ed610d8
Revises: 43c9ee2f7580
Create Date: 2025-04-17 20:08:13.149899

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7acf5ed610d8'
down_revision: Union[str, None] = '43c9ee2f7580'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('holdings', sa.Column('datatype', sa.Integer(), nullable=False))
    op.alter_column('holdings', 'ticker',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('holdings', 'quantity',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('holdings', 'quantity',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               nullable=False)
    op.alter_column('holdings', 'ticker',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.drop_column('holdings', 'datatype')
    # ### end Alembic commands ###
