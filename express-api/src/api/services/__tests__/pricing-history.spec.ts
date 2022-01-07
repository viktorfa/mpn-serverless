import { addDays } from "date-fns";
import { fillPricingHistory } from "../pricing-history";

describe("pricing-history fill", () => {
  it("should fill in pricing history", () => {
    const actual = fillPricingHistory({
      pricingHistory: [
        {
          date: "2021-09-02",
          pricing: { price: 100, currency: "NOK" },
          uri: "123",
        },
      ],
    });
    console.log("actual");
    console.log(actual);
    expect(actual.length).toBe(34);
    expect(actual[0].pricing.price).toBe(100);
    expect(actual[actual.length - 1].pricing.price).toBe(100);
  });
  it("should fill in pricing history when several history objects", () => {
    const actual = fillPricingHistory({
      pricingHistory: [
        {
          date: "2021-09-02",
          pricing: { price: 100, currency: "NOK" },
          uri: "123",
        },
        {
          date: "2021-09-10",
          pricing: { price: 120, currency: "NOK" },
          uri: "123",
        },
      ],
    });
    console.log("actual");
    console.log(actual);
    expect(actual.length).toBe(34);
    expect(actual[0].pricing.price).toBe(100);
    expect(actual[actual.length - 1].pricing.price).toBe(120);
  });
  it("should fill in pricing history when only price from today", () => {
    const actual = fillPricingHistory({
      pricingHistory: [
        {
          date: new Date().toISOString().split("T")[0],
          pricing: { price: 120, currency: "NOK" },
          uri: "123",
        },
      ],
    });
    expect(actual.length).toBe(1);
    expect(actual[0].pricing.price).toBe(120);
  });
  it("should fill in pricing history when have price of today", () => {
    const actual = fillPricingHistory({
      pricingHistory: [
        {
          date: addDays(new Date(), -5).toISOString().split("T")[0],
          pricing: { price: 100, currency: "NOK" },
          uri: "123",
        },
        {
          date: new Date().toISOString().split("T")[0],
          pricing: { price: 120, currency: "NOK" },
          uri: "123",
        },
      ],
    });
    expect(actual.length).toBe(6);
    expect(actual[0].pricing.price).toBe(100);
    expect(actual[actual.length - 1].pricing.price).toBe(120);
  });
});
