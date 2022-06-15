import { addDays } from "date-fns";
import { fillPricingHistory } from "../pricing-history";

describe("pricing-history fill", () => {
  it("should fill in pricing history", () => {
    const now = new Date();
    const actual = fillPricingHistory({
      pricingHistory: [
        {
          date: addDays(now, -33).toISOString().split("T")[0],
          pricing: { price: 100, currency: "NOK" },
          uri: "123",
        },
      ],
    });
    console.log("actual");
    console.log(actual);
    expect(actual.length).toBe(33);
    expect(actual[0].pricing.price).toBe(100);
    expect(actual[actual.length - 1].pricing.price).toBe(100);
  });
  it("should fill in pricing history when several history objects", () => {
    const now = new Date();
    const actual = fillPricingHistory({
      pricingHistory: [
        {
          date: addDays(now, -33).toISOString().split("T")[0],
          pricing: { price: 100, currency: "NOK" },
          uri: "123",
        },
        {
          date: addDays(now, -27).toISOString().split("T")[0],
          pricing: { price: 120, currency: "NOK" },
          uri: "123",
        },
      ],
    });
    console.log("actual");
    console.log(actual);
    expect(actual.length).toBe(33);
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
  it("should fill in pricing history when have price of yesterday", () => {
    const actual = fillPricingHistory({
      pricingHistory: [
        {
          date: addDays(new Date(), -5).toISOString().split("T")[0],
          pricing: { price: 100, currency: "NOK" },
          uri: "123",
        },
        {
          date: addDays(new Date(), -1).toISOString().split("T")[0],
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
