"""empty message

Revision ID: ee935258a72f
Revises: 
Create Date: 2021-11-03 16:56:21.348009

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ee935258a72f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('slug_reservation',
    sa.Column('slug', sa.String(), nullable=False),
    sa.Column('by', sa.String(), nullable=False),
    sa.Column('permanent', sa.Boolean(), nullable=True),
    sa.Column('created', sa.TIMESTAMP(), nullable=True),
    sa.Column('expires', sa.TIMESTAMP(), nullable=True),
    sa.PrimaryKeyConstraint('slug')
    )
    op.create_table('url_entry_model',
    sa.Column('companySlug', sa.String(), nullable=False),
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('recordId', sa.String(), nullable=True),
    sa.Column('longUrl', sa.String(), nullable=True),
    sa.Column('used', sa.BIGINT(), nullable=True),
    sa.Column('lastUsed', sa.TIMESTAMP(), nullable=True),
    sa.PrimaryKeyConstraint('companySlug', 'id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('url_entry_model')
    op.drop_table('slug_reservation')
    # ### end Alembic commands ###