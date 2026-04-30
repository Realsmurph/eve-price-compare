"""initial schema

Revision ID: 20260430_0001
Revises:
Create Date: 2026-04-30
"""

from alembic import op
import sqlalchemy as sa


revision = "20260430_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "eve_types",
        sa.Column("type_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=True),
        sa.Column("market_group_id", sa.Integer(), nullable=True),
        sa.Column("published", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("type_id"),
    )
    op.create_index(op.f("ix_eve_types_type_id"), "eve_types", ["type_id"], unique=False)
    op.create_index(op.f("ix_eve_types_name"), "eve_types", ["name"], unique=False)
    op.create_index(op.f("ix_eve_types_group_id"), "eve_types", ["group_id"], unique=False)
    op.create_index(
        op.f("ix_eve_types_market_group_id"),
        "eve_types",
        ["market_group_id"],
        unique=False,
    )

    op.create_table(
        "market_prices",
        sa.Column("type_id", sa.Integer(), nullable=False),
        sa.Column("buy", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("sell", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.PrimaryKeyConstraint("type_id"),
    )
    op.create_index(op.f("ix_market_prices_type_id"), "market_prices", ["type_id"], unique=False)

    op.create_table(
        "reaction_inputs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reaction_type_id", sa.Integer(), nullable=False),
        sa.Column("input_type_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("activity_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reaction_inputs_id"), "reaction_inputs", ["id"], unique=False)
    op.create_index(
        op.f("ix_reaction_inputs_reaction_type_id"),
        "reaction_inputs",
        ["reaction_type_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_reaction_inputs_input_type_id"),
        "reaction_inputs",
        ["input_type_id"],
        unique=False,
    )

    op.create_table(
        "reaction_recipes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reaction_type_id", sa.Integer(), nullable=False),
        sa.Column("output_type_id", sa.Integer(), nullable=False),
        sa.Column("output_quantity", sa.Integer(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("activity_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reaction_recipes_id"), "reaction_recipes", ["id"], unique=False)
    op.create_index(
        op.f("ix_reaction_recipes_reaction_type_id"),
        "reaction_recipes",
        ["reaction_type_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_reaction_recipes_output_type_id"),
        "reaction_recipes",
        ["output_type_id"],
        unique=True,
    )

    op.create_table(
        "watchlist_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("item_type_id", sa.Integer(), nullable=False),
        sa.Column("item_name", sa.String(length=255), nullable=False),
        sa.Column("target_price", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_watchlist_items_id"), "watchlist_items", ["id"], unique=False)
    op.create_index(
        op.f("ix_watchlist_items_item_type_id"),
        "watchlist_items",
        ["item_type_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_watchlist_items_item_name"),
        "watchlist_items",
        ["item_name"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_watchlist_items_item_name"), table_name="watchlist_items")
    op.drop_index(op.f("ix_watchlist_items_item_type_id"), table_name="watchlist_items")
    op.drop_index(op.f("ix_watchlist_items_id"), table_name="watchlist_items")
    op.drop_table("watchlist_items")

    op.drop_index(op.f("ix_reaction_recipes_output_type_id"), table_name="reaction_recipes")
    op.drop_index(op.f("ix_reaction_recipes_reaction_type_id"), table_name="reaction_recipes")
    op.drop_index(op.f("ix_reaction_recipes_id"), table_name="reaction_recipes")
    op.drop_table("reaction_recipes")

    op.drop_index(op.f("ix_reaction_inputs_input_type_id"), table_name="reaction_inputs")
    op.drop_index(op.f("ix_reaction_inputs_reaction_type_id"), table_name="reaction_inputs")
    op.drop_index(op.f("ix_reaction_inputs_id"), table_name="reaction_inputs")
    op.drop_table("reaction_inputs")

    op.drop_index(op.f("ix_market_prices_type_id"), table_name="market_prices")
    op.drop_table("market_prices")

    op.drop_index(op.f("ix_eve_types_market_group_id"), table_name="eve_types")
    op.drop_index(op.f("ix_eve_types_group_id"), table_name="eve_types")
    op.drop_index(op.f("ix_eve_types_name"), table_name="eve_types")
    op.drop_index(op.f("ix_eve_types_type_id"), table_name="eve_types")
    op.drop_table("eve_types")
