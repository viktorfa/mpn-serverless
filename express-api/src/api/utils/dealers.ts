export const getDealersForMarket = ({
  market,
  productCollection,
}: {
  market: string;
  productCollection: string;
}) => {
  if (market === "no") {
    if (productCollection === "groceryoffers") {
      return ["meny", "kolonial", "europris", "foodora_no", "bunnpris_no"];
    }
  } else if (market === "se") {
    if (productCollection === "segroceryoffers") {
      return [
        "hemkop",
        "coop_online",
        "mat_se",
        "wolt_se",
        "stora_coop",
        "matsmart",
        "ica_online",
      ];
    }
  } else if (market === "dk") {
    if (productCollection === "dkgroceryoffers") {
      return [
        "bevco_dk",
        "bilkatogo",
        "nemlig",
        "rema1000_dk",
        "motatos_dk",
        "pandasia_dk",
      ];
    }
  } else if (market === "de") {
    if (productCollection === "degroceryoffers") {
      return [
        "rewe_de",
        "mytime_de",
        "lebensmittel_versand",
        "supermarkt24h",
        "motatos_de",
        "netto_de",
        "kaufland",
        "edeka24",
        "aldi_sued",
      ];
    }
  }
  return [];
};
