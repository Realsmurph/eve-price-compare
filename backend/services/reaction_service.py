from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import (
    ITL_AMARR_JF_LOAD_FEE,
    ITL_AMARR_RATE_PER_M3,
    ITL_AMARR_ROUTE,
    ITL_JF_LOAD_VOLUME_M3,
    ITL_JITA_JF_LOAD_FEE,
    ITL_JITA_RATE_PER_M3,
    ITL_JITA_ROUTE,
    ITL_SHIPPING_DEFAULT_ORIGIN,
    ITL_SHIPPING_PROVIDER,
)
from ..models import EveType, MarketPrice, ReactionInput, ReactionRecipe
from ..schemas import ReactionLineItem, ReactionProfitRead


REACTION_ACTIVITY_ID = 11


class ReactionNotFoundError(LookupError):
    pass


class MissingPriceError(LookupError):
    pass


class ReactionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def calculate_profit(
        self,
        type_id: int,
        import_rate: Decimal = Decimal("0"),
        import_flat_fee: Decimal = Decimal("0"),
        shipping_origin: str | None = None,
        shipping_rate_per_m3: Decimal | None = None,
        shipping_jf_load_fee: Decimal | None = None,
    ) -> ReactionProfitRead:
        recipe = self._get_recipe(type_id)
        if recipe is None:
            raise ReactionNotFoundError(f"No reaction recipe found for type_id {type_id}")

        inputs = self._get_inputs(recipe.reaction_type_id)
        if not inputs:
            raise ReactionNotFoundError(
                f"No activity 11 inputs found for reaction type_id {recipe.reaction_type_id}"
            )

        shipping_terms = _shipping_terms(
            shipping_origin or ITL_SHIPPING_DEFAULT_ORIGIN,
            shipping_rate_per_m3=shipping_rate_per_m3,
            shipping_jf_load_fee=shipping_jf_load_fee,
        )
        input_lines = [self._build_input_line(item) for item in inputs]
        input_cost = sum((line.total for line in input_lines), Decimal("0"))
        input_volume_m3 = sum(
            (line.total_volume_m3 or Decimal("0") for line in input_lines),
            Decimal("0"),
        )
        shipping_cost = _calculate_shipping_cost(input_volume_m3, shipping_terms)

        output_price = self._get_output_price(recipe.output_type_id)
        output_value = output_price * Decimal(recipe.output_quantity)
        import_cost = (input_cost * import_rate) + import_flat_fee + shipping_cost
        total_cost = input_cost + import_cost
        profit = output_value - input_cost
        profit_after_import = output_value - total_cost
        margin = (profit / input_cost) if input_cost > 0 else None
        margin_after_import = (profit_after_import / total_cost) if total_cost > 0 else None
        isk_per_hour = profit * Decimal(3600) / Decimal(recipe.duration_seconds)
        isk_per_hour_after_import = (
            profit_after_import * Decimal(3600) / Decimal(recipe.duration_seconds)
        )
        output_type = self.db.get(EveType, recipe.output_type_id)

        return ReactionProfitRead(
            type_id=type_id,
            reaction_type_id=recipe.reaction_type_id,
            output_type_id=recipe.output_type_id,
            output_name=output_type.name if output_type else None,
            output_quantity=recipe.output_quantity,
            duration_seconds=recipe.duration_seconds,
            input_cost=input_cost,
            input_volume_m3=input_volume_m3,
            shipping_provider=ITL_SHIPPING_PROVIDER,
            shipping_route=shipping_terms.route,
            shipping_origin=shipping_terms.origin,
            shipping_rate_per_m3=shipping_terms.rate_per_m3,
            shipping_jf_load_volume_m3=ITL_JF_LOAD_VOLUME_M3,
            shipping_jf_load_fee=shipping_terms.jf_load_fee,
            shipping_cost=shipping_cost,
            import_cost=import_cost,
            total_cost=total_cost,
            output_value=output_value,
            profit=profit,
            profit_after_import=profit_after_import,
            margin=margin,
            margin_after_import=margin_after_import,
            isk_per_hour=isk_per_hour,
            isk_per_hour_after_import=isk_per_hour_after_import,
            inputs=input_lines,
        )

    def _get_recipe(self, type_id: int) -> ReactionRecipe | None:
        statement = (
            select(ReactionRecipe)
            .where(ReactionRecipe.activity_id == REACTION_ACTIVITY_ID)
            .where(
                (ReactionRecipe.output_type_id == type_id)
                | (ReactionRecipe.reaction_type_id == type_id)
            )
        )
        return self.db.scalars(statement).first()

    def _get_inputs(self, reaction_type_id: int) -> list[ReactionInput]:
        statement = (
            select(ReactionInput)
            .where(ReactionInput.activity_id == REACTION_ACTIVITY_ID)
            .where(ReactionInput.reaction_type_id == reaction_type_id)
            .order_by(ReactionInput.input_type_id.asc())
        )
        return list(self.db.scalars(statement))

    def _build_input_line(self, item: ReactionInput) -> ReactionLineItem:
        unit_price = self._get_input_price(item.input_type_id)
        eve_type = self.db.get(EveType, item.input_type_id)
        quantity = item.quantity
        unit_volume = Decimal(eve_type.volume) if eve_type and eve_type.volume is not None else None
        total_volume = unit_volume * Decimal(quantity) if unit_volume is not None else None

        return ReactionLineItem(
            type_id=item.input_type_id,
            name=eve_type.name if eve_type else None,
            quantity=quantity,
            unit_price=unit_price,
            total=unit_price * Decimal(quantity),
            unit_volume_m3=unit_volume,
            total_volume_m3=total_volume,
        )

    def _get_input_price(self, type_id: int) -> Decimal:
        price = self.db.get(MarketPrice, type_id)
        if price is None or price.sell is None:
            raise MissingPriceError(f"Missing sell price for input type_id {type_id}")
        return Decimal(price.sell)

    def _get_output_price(self, type_id: int) -> Decimal:
        price = self.db.get(MarketPrice, type_id)
        if price is None or price.buy is None:
            raise MissingPriceError(f"Missing buy price for output type_id {type_id}")
        return Decimal(price.buy)


class ShippingTerms:
    def __init__(
        self,
        origin: str,
        route: str,
        rate_per_m3: Decimal,
        jf_load_fee: Decimal,
    ) -> None:
        self.origin = origin
        self.route = route
        self.rate_per_m3 = rate_per_m3
        self.jf_load_fee = jf_load_fee


def _shipping_terms(
    origin: str,
    shipping_rate_per_m3: Decimal | None = None,
    shipping_jf_load_fee: Decimal | None = None,
) -> ShippingTerms:
    normalized_origin = origin.strip().lower()
    if normalized_origin == "amarr":
        return ShippingTerms(
            origin="amarr",
            route=ITL_AMARR_ROUTE,
            rate_per_m3=shipping_rate_per_m3 or ITL_AMARR_RATE_PER_M3,
            jf_load_fee=shipping_jf_load_fee or ITL_AMARR_JF_LOAD_FEE,
        )

    return ShippingTerms(
        origin="jita",
        route=ITL_JITA_ROUTE,
        rate_per_m3=shipping_rate_per_m3 or ITL_JITA_RATE_PER_M3,
        jf_load_fee=shipping_jf_load_fee or ITL_JITA_JF_LOAD_FEE,
    )


def _calculate_shipping_cost(volume_m3: Decimal, terms: ShippingTerms) -> Decimal:
    if volume_m3 <= 0:
        return Decimal("0")

    full_loads = int(volume_m3 // ITL_JF_LOAD_VOLUME_M3)
    remainder = volume_m3 % ITL_JF_LOAD_VOLUME_M3
    full_load_cost = Decimal(full_loads) * terms.jf_load_fee
    if remainder == 0:
        return full_load_cost

    remainder_cost = min(remainder * terms.rate_per_m3, terms.jf_load_fee)
    return full_load_cost + remainder_cost
