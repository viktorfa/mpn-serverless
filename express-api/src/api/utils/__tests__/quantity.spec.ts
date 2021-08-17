import { getValueObject } from "../quantity";

describe("quantity", () => {
  it("should get value from a quantity object and price", () => {
    const actual = getValueObject({
      price: 10,
      quantity: {
        unit: { symbol: "m", si: { factor: 1, symbol: "m" }, type: "measure" },
        amount: { min: 1, max: 1 },
        standard: { max: 1, min: 1 },
      },
    });
  });
});
