const { assert } = require("chai");
const _ = require("lodash");
const allProducts = require("../../assets/all-products.json");
const {
  createProductObjects,
  getLunrIndex,
  getAutocompleteData,
} = require("../lib");

it("should create objects", () => {
  const actual = createProductObjects(allProducts);
  assert.isDefined(actual);
  assert.isObject(actual);
  assert.equal(Object.keys(actual).length, allProducts.length);
});

describe("getLunrIndex", () => {
  it("should get a lunr index", () => {
    const actual = getLunrIndex(_.take(allProducts, 1000));
    assert.isDefined(actual);
    assert.isObject(actual);
    assert.isFunction(actual.toJSON);
  });

  it("should not use naive English language stemming", () => {
    const lunrIndex = getLunrIndex(allProducts);
    const tokens = Object.keys(lunrIndex.invertedIndex);
    assert.include(tokens, "medisterkaker");
  });
});

describe("getAutocompleteData", () => {
  it("should return an object", () => {
    assert.isObject(getAutocompleteData([]));
    assert.isObject(getAutocompleteData(_.take(allProducts, 100)));
  });
  it("should have correct fields", () => {
    const actual = getAutocompleteData(_.take(allProducts, 100));
    const expectedFields = [
      "heading_tokens",
      "heading_bigrams",
      "heading_fullgrams",
    ];
    expectedFields.forEach((field) => {
      assert.isArray(actual[field]);
      assert.isString(actual[field][0]);
    });
  });
  it("should have correct values", () => {
    const exampleProducts = [
      {
        title: "pizza grandiosa mozzarella 4pk",
      },
      {
        title: "pizza grandiosa picante",
      },
      {
        title: "apetina picante mozzarella",
      },
      {
        title: "apetina picante mozzarella",
      },
    ];
    const actual = getAutocompleteData(exampleProducts);
    const expectedTokens = [
      "pizza",
      "grandiosa",
      "mozzarella",
      "4pk",
      "picante",
      "apetina",
    ];
    const expectedBigrams = [
      "pizza grandiosa",
      "grandiosa mozzarella",
      "mozzarella 4pk",
      "grandiosa picante",
      "apetina picante",
      "picante mozzarella",
    ];
    const expectedFullgrams = [
      "pizza grandiosa mozzarella 4pk",
      "pizza grandiosa picante",
      "apetina picante mozzarella",
    ];

    expectedTokens.forEach((x) => {
      assert.include(actual.heading_tokens, x);
    });
    assert.equal(new Set(actual.heading_tokens).length, actual.length);

    expectedBigrams.forEach((x) => {
      assert.include(actual.heading_bigrams, x);
    });
    assert.equal(new Set(actual.heading_bigrams).length, actual.length);

    expectedFullgrams.forEach((x) => {
      assert.include(actual.heading_fullgrams, x);
    });
    assert.equal(new Set(actual.heading_fullgrams).length, actual.length);
  });
});
