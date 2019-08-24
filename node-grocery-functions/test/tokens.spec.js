const { assert } = require("chai");
const { getBigrams, getTokens, preprocessHeading } = require("../tokens");

describe("getBigrams", () => {
  it("should return an array", () => {
    assert.isArray(getBigrams([]));
    assert.isArray(getBigrams(["biff"]));
    assert.isArray(getBigrams(["big", "mac"]));
  });
  it("should work with two tokens", () => {
    const tokens = ["pizza", "grandiosa"];
    const expected = ["pizza grandiosa"];
    const actual = getBigrams(tokens);
    assert.deepEqual(actual, expected);
  });
  it("should work with three tokens", () => {
    const tokens = ["pizza", "grandiosa", "mozzarella"];
    const expected = ["pizza grandiosa", "grandiosa mozzarella"];
    const actual = getBigrams(tokens);
    assert.deepEqual(actual, expected);
  });
});

describe("getTokens", () => {
  it("should return an array", () => {
    assert.isArray(getTokens(""));
    assert.isArray(getTokens("biff"));
    assert.isArray(getTokens("big mac"));
    assert.isArray(getTokens("big mac xtra large"));
  });
  it("should work with two tokens", () => {
    const tokens = "pizza grandiosa";
    const expected = ["pizza", "grandiosa"];
    const actual = getTokens(tokens);
    assert.deepEqual(actual, expected);
  });
  it("should work with three tokens", () => {
    const tokens = "pizza grandiosa mozzarella";
    const expected = ["pizza", "grandiosa", "mozzarella"];
    const actual = getTokens(tokens);
    assert.deepEqual(actual, expected);
  });
});

describe("preprocessHeading", () => {
  it("should return a string", () => {
    assert.isString(preprocessHeading(""));
    assert.isString(preprocessHeading("pizza"));
    assert.isString(preprocessHeading("pizza grandiosa 4pk"));
    assert.isString(preprocessHeading("n&j arctic power"));
    assert.isString(preprocessHeading("non-stop, 4pk"));
  });
  it("should remove punctuation", () => {
    const string = "løvstek, 4pk";
    const expected = "løvstek 4pk";
    const actual = preprocessHeading(string);
    assert.strictEqual(actual, expected);
  });
  it("should trim and remove double whitespace", () => {
    const string = " løvstek    .4pk";
    const expected = "løvstek 4pk";
    const actual = preprocessHeading(string);
    assert.strictEqual(actual, expected);
  });
  it("should make lower case", () => {
    const string = "Tine Smør";
    const expected = "tine smør";
    const actual = preprocessHeading(string);
    assert.strictEqual(actual, expected);
  });
});
