export const siMappings = {
  g: { symbol: "kg", factor: 0.001 },
  hg: { symbol: "kg", factor: 0.01 },
  dg: { symbol: "kg", factor: 0.1 },
  kg: { symbol: "kg", factor: 1 },
  ml: { symbol: "l", factor: 0.001 },
  hl: { symbol: "l", factor: 0.01 },
  dl: { symbol: "l", factor: 0.1 },
  l: { symbol: "l", factor: 1 },
  mm: { symbol: "m", factor: 0.001 },
  cm: { symbol: "m", factor: 0.01 },
  dm: { symbol: "m", factor: 0.1 },
  m: { symbol: "m", factor: 1 },
  m2: { symbol: "m2", factor: 1 },
};

export const getQuantityObject = ({
  quantityUnit,
  quantityValue,
}): Quantity => {
  const siConfig = siMappings[quantityUnit];
  const unit = { si: siConfig, symbol: quantityUnit, type: "quantity" };
  const amount = { min: quantityValue, max: quantityValue };
  const standardValue = getStandardSiAmount({
    siConfig,
    value: quantityValue,
  });
  const standard = { min: standardValue, max: standardValue };
  return { standard, amount, unit };
};

export const getValueObject = ({
  price,
  quantity,
}: {
  price: number;
  quantity: Quantity;
}): Quantity => {
  const amountValue = price / quantity.amount.min;
  const standardValue = price / quantity.standard.min;

  return {
    standard: { min: standardValue, max: standardValue },
    unit: quantity.unit,
    amount: { min: amountValue, max: amountValue },
  };
};

export const getStandardSiAmount = ({
  siConfig,
  value,
  invert = false,
}: {
  siConfig: SiConfig;
  value: number;
  invert?: boolean;
}) => {
  if (invert) {
    return value / siConfig.factor;
  } else {
    return value * siConfig.factor;
  }
};
