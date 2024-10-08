export const getUri = (uri: string): string => {
  const uriParts = uri.split(":");
  const dealer = uriParts[0];
  const sku = uriParts.length === 3 ? uriParts[2] : uriParts[1];
  return `${dealer}:${sku}`;
};

export function getSIUnit(
  unit: string,
): { symbol: string; factor: number } | null {
  if (!unit) return null;

  const unitLower = unit.toLowerCase();
  switch (unitLower) {
    case "kg":
      return { symbol: "kg", factor: 1 };
    case "hg":
      return { symbol: "kg", factor: 0.1 };
    case "dg":
      return { symbol: "kg", factor: 0.01 };
    case "g":
      return { symbol: "kg", factor: 1e-3 };
    case "mg":
      return { symbol: "kg", factor: 1e-6 };
    case "l":
    case "lt":
    case "liter":
    case "litre":
      return { symbol: "l", factor: 1 };
    case "ml":
      return { symbol: "l", factor: 1e-3 };
    case "cl":
      return { symbol: "l", factor: 1e-2 };
    case "dl":
      return { symbol: "l", factor: 1e-1 };
    case "mm":
      return { symbol: "m", factor: 1e-3 };
    case "cm":
      return { symbol: "m", factor: 1e-2 };
    case "dm":
      return { symbol: "m", factor: 1e-1 };
    case "m":
      return { symbol: "m", factor: 1 };
    default:
      return null;
  }
}

export function standardizeQuantity(
  unit: string,
  amount: number,
): number | null {
  if (!unit || amount == null) return null;

  const unitLower = unit.toLowerCase();
  switch (unitLower) {
    case "mg":
      return amount / 1e6; // milligrams to kilograms
    case "g":
      return amount / 1000; // grams to kilograms
    case "hg":
      return amount / 10; // grams to kilograms
    case "kg":
      return amount; // already in kilograms
    case "ml":
      return amount / 1000; // milliliters to liters
    case "cl":
      return amount / 100; // milliliters to liters
    case "dl":
      return amount / 10; // milliliters to liters
    case "l":
    case "lt":
    case "liter":
    case "litre":
      return amount; // already in liters
    case "mm":
      return amount / 1000; // already in meters
    case "cm":
      return amount / 100; // already in meters
    case "dm":
      return amount / 10; // already in meters
    case "m":
      return amount; // already in meters
    default:
      return amount; // Return as is if unit is unrecognized
  }
}

type NewOfferType = {
  uri: string;
  title: string;
  href: string;
  ahref?: string;
  dealer_key: string;
  valid_through: string;
  price?: number;
  price_unit?: string;
  currency?: string;
  dealerObject?: {
    key: string;
    market: string;
    title: string;
  };
};

type ProductType = {
  quantity_unit?: string;
  quantity_amount?: number;
};

export function convertDenormalizedOffer({
  newOffer,
  product,
}: {
  newOffer: NewOfferType;
  product?: ProductType;
}): any {
  const [dealer, sku] = newOffer.uri.split(":");
  // Must keep old urls on frontend
  const uri = `${dealer}:product:${sku}`;

  const quantity = getQuantity({
    unit: product?.quantity_unit,
    amount: product?.quantity_amount,
  });
  const rawValue = newOffer.price / product?.quantity_amount;
  const value = getValue({
    unit: product?.quantity_unit,
    amount: rawValue,
  });

  return {
    // '_id': undefined, // No _id in new format; can omit or generate if necessary
    title: newOffer.title,
    uri,
    href: newOffer.href,
    mpnStock: newOffer.mpn_stock, // Default value as it's not available
    pricing: {
      price: newOffer.price,
      currency: newOffer.currency,
      prePrice: newOffer.pre_price || null,
      priceUnit: newOffer.price_unit || null,
    },
    // 'siteCollection': newOffer.siteCollection || null, // Not available
    validThrough: newOffer.valid_through,
    market: newOffer.market,
    ahref: newOffer.ahref || null,
    // 'isPartner': false, // Not available; default to false if necessary
    // 'pageviews': newOffer.pageviews || 0, // Not available
    dealerKey: newOffer.dealer_key,

    // 'isRecent': true, // Not available; default to true if necessary
    // 'value': newOffer.value || null, // Not available
    quantity,
    value,
    dealerObject: newOffer.dealerObject
      ? {
          key: newOffer.dealerObject.key,
          logoUrl: newOffer.dealerObject.logo_url || null,
          market: newOffer.dealerObject.market,
          text: newOffer.dealerObject.title || null,
          url: newOffer.dealerObject.url || null,
        }
      : null,
  };
}

type LegacyQuantityType = {
  size: {
    unit: {
      symbol: string;
      si: {
        symbol: string;
        factor: number;
      };
    };
    amount: {
      min: number;
      max: number;
    };
    standard: {
      min: number;
      max: number;
    };
  };
};

export const getQuantity = ({
  unit,
  amount,
}: {
  unit?: string;
  amount?: number;
}): LegacyQuantityType | null => {
  const siUnit = getSIUnit(unit);
  const standardizedAmount = standardizeQuantity(unit, amount);

  if (!unit || !amount) {
    return null;
  }

  return {
    size: {
      unit: {
        symbol: unit,
        si: siUnit,
      },
      amount: {
        min: amount,
        max: amount,
      },
      standard: {
        min: standardizedAmount,
        max: standardizedAmount,
      },
    },
  };
};
export const getValue = ({
  unit,
  amount,
}: {
  unit?: string;
  amount?: number;
}): LegacyQuantityType | null => {
  if (!unit || !amount) {
    return null;
  }
  const siUnit = getSIUnit(unit);
  if (!siUnit) {
    return null;
  }
  const standardizedAmount = standardizeQuantity(unit, amount) / siUnit.factor;

  return {
    size: {
      unit: {
        symbol: unit,
        si: siUnit,
      },
      amount: {
        min: amount,
        max: amount,
      },
      standard: {
        min: standardizedAmount,
        max: standardizedAmount,
      },
    },
  };
};

export function convertDenormalizedProduct(newProduct: any): any {
  return {
    _id: newProduct.product_id,
    brand: newProduct.brand,
    brandKey: newProduct.brand_key,
    gtins: newProduct.gtins,
    imageUrl: newProduct.image_url || null,
    // 'mpnIngredients': null, // Not required
    mpnNutrition: newProduct.nutrition || null,
    // 'mpnProperties': {}, // Not required
    quantity: getQuantity({
      unit: newProduct.quantity_unit,
      amount: parseFloat(newProduct.quantity_amount),
    }),
    offers: newProduct.offers
      ? newProduct.offers.map((offer) =>
          convertDenormalizedOffer({ newOffer: offer, product: newProduct }),
        )
      : [],
    priceMin: parseFloat(newProduct.price_min) || null,
    priceMax: parseFloat(newProduct.price_max) || null,
    valueMin: parseFloat(newProduct.value_min) || null,
    valueMax: parseFloat(newProduct.value_max) || null,
    validThrough: newProduct.valid_through,
    // 'pageviews': 0, // Not available; default to 0 if necessary
    title: newProduct.title,
    subtitle: newProduct.subtitle || null,
    shortDescription: newProduct.short_description || null,
    description: newProduct.description || null,
    // 'mpnCategories': [], // Not available; can omit
    // 'score': 0, // Not required
  };
}

export const getCommaSeparatedAsList = (str?: string): string[] => {
  if (!str) return [];
  return str.split(",").filter(Boolean);
};
