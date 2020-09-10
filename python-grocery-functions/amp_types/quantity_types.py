from typing import TypedDict


class QuantityAmount(TypedDict):
    min: float
    max: float


class SiConfig(TypedDict):
    factor: float
    symbol: str


class QuantityUnit(TypedDict):
    symbol: str
    type: str
    si: SiConfig


class Quantity(TypedDict):
    unit: QuantityUnit
    amount: QuantityAmount
    standard: QuantityAmount


class QuantityField(TypedDict):
    size: Quantity
    pieces: Quantity


class ItemsField(TypedDict):
    amount: QuantityAmount


class ExtractQuantityReturnType(TypedDict):
    size: Quantity
    pieces: Quantity
    value: QuantityField
    items: ItemsField
