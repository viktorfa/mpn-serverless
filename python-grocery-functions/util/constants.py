si_mappings = dict(
    g=dict(symbol='kg', factor=0.001),
    hg=dict(symbol='kg', factor=0.01),
    dg=dict(symbol='kg', factor=0.1),
    kg=dict(symbol='kg', factor=1),

    ml=dict(symbol='l', factor=0.001),
    hl=dict(symbol='l', factor=0.01),
    dl=dict(symbol='l', factor=0.1),
    l=dict(symbol='l', factor=1),
)
piece_units = [
    'stk',
    'boks',
    'flaske',
]

quantity_units = [key for key, _ in si_mappings.items()]

quantity_value_units = ['/{}'.format(x) for x in quantity_units]
quantity_value_units.extend(['kr/{}'.format(x) for x in quantity_units])
quantity_value_units.extend(['kr{}'.format(x) for x in quantity_units])
piece_value_units = ['/{}'.format(x) for x in piece_units]
piece_value_units.extend(['kr/{}'.format(x) for x in piece_units])
piece_value_units.extend(['kr{}'.format(x) for x in piece_units])
