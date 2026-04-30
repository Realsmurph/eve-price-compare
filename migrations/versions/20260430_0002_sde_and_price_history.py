"""sde metadata and market price history

Revision ID: 20260430_0002
Revises: 20260430_0001
Create Date: 2026-04-30
"""

from alembic import op
import sqlalchemy as sa


revision = "20260430_0002"
down_revision = "20260430_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("eve_types", sa.Column("group_name", sa.String(length=255), nullable=True))
    op.add_column("eve_types", sa.Column("category_id", sa.Integer(), nullable=True))
    op.add_column("eve_types", sa.Column("category_name", sa.String(length=255), nullable=True))
    op.add_column("eve_types", sa.Column("volume", sa.Numeric(precision=18, scale=4), nullable=True))
    op.create_index(op.f("ix_eve_types_group_name"), "eve_types", ["group_name"], unique=False)
    op.create_index(op.f("ix_eve_types_category_id"), "eve_types", ["category_id"], unique=False)
    op.create_index(op.f("ix_eve_types_category_name"), "eve_types", ["category_name"], unique=False)

    op.create_table(
        "market_price_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("type_id", sa.Integer(), nullable=False),
        sa.Column("hub", sa.String(length=32), nullable=False),
        sa.Column("buy", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("sell", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("history_date", sa.Date(), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("type_id", "hub", "observed_at", name="uq_market_price_history_snapshot"),
    )
    op.create_index(op.f("ix_market_price_history_id"), "market_price_history", ["id"], unique=False)
    op.create_index(
        op.f("ix_market_price_history_type_id"),
        "market_price_history",
        ["type_id"],
        unique=False,
    )
    op.create_index(op.f("ix_market_price_history_hub"), "market_price_history", ["hub"], unique=False)
    op.create_index(
        op.f("ix_market_price_history_history_date"),
        "market_price_history",
        ["history_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_market_price_history_history_date"), table_name="market_price_history")
    op.drop_index(op.f("ix_market_price_history_hub"), table_name="market_price_history")
    op.drop_index(op.f("ix_market_price_history_type_id"), table_name="market_price_history")
    op.drop_index(op.f("ix_market_price_history_id"), table_name="market_price_history")
    op.drop_table("market_price_history")

    op.drop_index(op.f("ix_eve_types_category_name"), table_name="eve_types")
    op.drop_index(op.f("ix_eve_types_category_id"), table_name="eve_types")
    op.drop_index(op.f("ix_eve_types_group_name"), table_name="eve_types")
    op.drop_column("eve_types", "volume")
    op.drop_column("eve_types", "category_name")
    op.drop_column("eve_types", "category_id")
    op.drop_column("eve_types", "group_name")
