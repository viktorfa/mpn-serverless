alt_unit_map = {
    "milliliter": "ml",
    "centiliter": "cl",
    "desiliter": "dl",
    "liter": "l",
    "ltr": "l",
    "kilogram": "kg",
    "kilo": "kg",
    "hektogram": "hg",
    "gr": "g",
    "gram": "g",
    "m²": "m2",
    "kvm": "m2",
    "sqm": "m2",
    "lm": "m",
    "meter": "m",
}

si_mappings = dict(
    g=dict(symbol="kg", factor=0.001),
    cg=dict(symbol="kg", factor=0.01),
    hg=dict(symbol="kg", factor=0.1),
    dg=dict(symbol="kg", factor=0.1),
    kg=dict(symbol="kg", factor=1),
    ml=dict(symbol="l", factor=0.001),
    cl=dict(symbol="l", factor=0.01),
    dl=dict(symbol="l", factor=0.1),
    l=dict(symbol="l", factor=1),
    mm=dict(symbol="m", factor=0.001),
    cm=dict(symbol="m", factor=0.01),
    dm=dict(symbol="m", factor=0.1),
    m=dict(symbol="m", factor=1),
    m2=dict(symbol="m2", factor=1),
)
piece_units = [
    "stk",
    "boks",
    "flaske",
]

quantity_units = sorted(
    [key for key in [*si_mappings.keys(), *alt_unit_map.keys()]], key=len, reverse=True
)

quantity_value_units = ["/{}".format(x) for x in quantity_units]
quantity_value_units.extend(["kr/{}".format(x) for x in quantity_units])
quantity_value_units.extend(["kr{}".format(x) for x in quantity_units])
piece_value_units = ["/{}".format(x) for x in piece_units]
piece_value_units.extend(["kr/{}".format(x) for x in piece_units])
piece_value_units.extend(["kr{}".format(x) for x in piece_units])
