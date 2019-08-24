"""Using some typing_extensions some of which will be part of Python from 3.8.
https://github.com/python/typing/blob/master/typing_extensions/README.rst
"""

# TypedDict: https://www.python.org/dev/peps/pep-0589/
from typing_extensions import TypedDict


class QuantityAmount(TypedDict):
    min: float
    max: float


class QuantityUnit(TypedDict):
    symbol: str
    type: str


class Quantity(TypedDict):
    unit: QuantityUnit
    amount: QuantityAmount


class QuantityField(TypedDict):
    size = Quantity,
    pieces = Quantity


class Value(TypedDict):
    unit: QuantityUnit
    amount: QuantityAmount
    currency: str


class ValueField(TypedDict):
    size: Value
    pieces: Value


class ItemsField(TypedDict):
    amount: QuantityAmount


class ExtractQuantityReturnType(TypedDict):
    quantity: QuantityField
    value: ValueField
    items: ItemsField
