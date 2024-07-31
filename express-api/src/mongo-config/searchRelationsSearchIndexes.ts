import urllib from "urllib";
import { mongoDatabase } from "../config/vars";

const searchIndexMappings = {
  dynamic: false,
  fields: {
    brand: {
      analyzer: "diacriticFolderStandard",
      indexOptions: "positions",
      searchAnalyzer: "diacriticFolderStandard",
      store: false,
      type: "string",
    },
    brandKey: {
      analyzer: "lucene.keyword",
      indexOptions: "docs",
      norms: "omit",
      searchAnalyzer: "lucene.keyword",
      store: false,
      type: "string",
    },
    mpnCategories: {
      fields: {
        key: {
          analyzer: "lucene.keyword",
          indexOptions: "docs",
          norms: "omit",
          searchAnalyzer: "lucene.keyword",
          store: false,
          type: "string",
        },
        name: {
          indexOptions: "positions",
          store: false,
          type: "string",
        },
      },
      type: "document",
    },
    mpnIngredients: {
      fields: {
        processedScore: {
          representation: "int64",
          type: "number",
        },
      },
      type: "document",
    },
    mpnNutrition: {
      fields: {
        carbohydrates: {
          fields: {
            value: {
              type: "number",
            },
          },
          type: "document",
        },
        energyKcal: {
          fields: {
            value: {
              type: "number",
            },
          },
          type: "document",
        },
        fats: {
          fields: {
            value: {
              type: "number",
            },
          },
          type: "document",
        },
        proteins: {
          fields: {
            value: {
              type: "number",
            },
          },
          type: "document",
        },
      },
      type: "document",
    },
    offers: {
      fields: {
        dealerKey: [
          {
            analyzer: "lucene.keyword",
            indexOptions: "docs",
            norms: "omit",
            searchAnalyzer: "lucene.keyword",
            store: false,
            type: "string",
          },
          {
            type: "stringFacet",
          },
        ],
        isPartner: {
          type: "boolean",
        },
        siteCollection: {
          analyzer: "lucene.keyword",
          indexOptions: "docs",
          norms: "omit",
          searchAnalyzer: "lucene.keyword",
          store: false,
          type: "string",
        },
        vendorKey: {
          analyzer: "lucene.keyword",
          indexOptions: "docs",
          norms: "omit",
          searchAnalyzer: "lucene.keyword",
          store: false,
          type: "string",
        },
      },
      type: "document",
    },
    pageviews: {
      indexDoubles: false,
      representation: "int64",
      type: "number",
    },
    priceMax: {
      type: "number",
    },
    priceMin: {
      type: "number",
    },
    quantity: {
      fields: {
        size: {
          fields: {
            standard: {
              fields: {
                max: {
                  type: "number",
                },
              },
              type: "document",
            },
          },
          type: "document",
        },
      },
      type: "document",
    },
    relationType: {
      analyzer: "lucene.keyword",
      indexOptions: "docs",
      norms: "omit",
      searchAnalyzer: "lucene.keyword",
      store: false,
      type: "string",
    },
    title: {
      analyzer: "diacriticFolderStandard",
      indexOptions: "positions",
      searchAnalyzer: "diacriticFolderStandard",
      store: false,
      type: "string",
    },
    valueMax: {
      type: "number",
    },
    valueMin: {
      type: "number",
    },
  },
};

const searchIndexAnalyzers = [
  {
    name: "diacriticFolderKeyword",
    charFilters: [],
    tokenizer: {
      type: "keyword",
    },
    tokenFilters: [
      {
        type: "icuFolding",
      },
    ],
  },
  {
    name: "diacriticFolderStandard",
    charFilters: [],
    tokenizer: {
      type: "standard",
      //maxGram: 6,
      //minGram: 4,
      //type: "nGram",
    },
    tokenFilters: [
      {
        type: "icuFolding",
      },
    ],
  },
];

const offersWithRelationsCollections = [
  "relations_with_offers_au",
  "relations_with_offers_de",
  "relations_with_offers_dk",
  "relations_with_offers_es",
  "relations_with_offers_fi",
  "relations_with_offers_fr",
  "relations_with_offers_it",
  "relations_with_offers_nl",
  "relations_with_offers_no",
  "relations_with_offers_pl",
  "relations_with_offers_se",
  "relations_with_offers_sg",
  "relations_with_offers_th",
  "relations_with_offers_uk",
  "relations_with_offers_us",
];

const updateAllSearchIndexes = async () => {
  const promises = [];
  for (const collectionName of offersWithRelationsCollections) {
    promises.push(updateSearchIndex({ collectionName }));
  }
  const result = await Promise.all(promises);
  return result;
};

const updateSearchIndex = async ({
  collectionName,
}: {
  collectionName: string;
}) => {
  const { ATLAS_USERNAME, ATLAS_PASSWORD } = process.env;
  const { data: getIndexesData, res: getIndexesResponse } =
    await urllib.request(
      `https://cloud.mongodb.com/api/atlas/v2/groups/5f34e67a4b0c737825269122/clusters/mpn-cluster/fts/indexes/${mongoDatabase}/${collectionName}`,
      {
        digestAuth: `${ATLAS_USERNAME}:${ATLAS_PASSWORD}`,
        headers: { Accept: "application/vnd.atlas.2023-02-01+json" },
      },
    );

  const getIndexesObject = JSON.parse(getIndexesData);

  console.log("getIndexesResponse");
  console.log(getIndexesData.toString());

  if (getIndexesObject.length === 0) {
    const { data: createIndexData, res: createIndexResponse } =
      await urllib.request(
        "https://cloud.mongodb.com/api/atlas/v2/groups/5f34e67a4b0c737825269122/clusters/mpn-cluster/fts/indexes",
        {
          method: "POST",
          digestAuth: `${ATLAS_USERNAME}:${ATLAS_PASSWORD}`,
          headers: {
            Accept: "application/vnd.atlas.2023-02-01+json",
            "Content-Type": "application/json",
          },
          data: {
            collectionName,
            database: mongoDatabase,
            name: "default",
            mappings: searchIndexMappings,
            analyzers: searchIndexAnalyzers,
          },
        },
      );

    console.log("createIndexResponse");
    console.log(createIndexData.toString());
    return JSON.parse(createIndexData);
  } else {
    const indexId = getIndexesObject[0].indexID;
    const { data: createIndexData, res: createIndexResponse } =
      await urllib.request(
        `https://cloud.mongodb.com/api/atlas/v2/groups/5f34e67a4b0c737825269122/clusters/mpn-cluster/fts/indexes/${indexId}`,
        {
          method: "PATCH",
          digestAuth: `${ATLAS_USERNAME}:${ATLAS_PASSWORD}`,
          headers: {
            Accept: "application/vnd.atlas.2023-02-01+json",
            "Content-Type": "application/json",
          },
          data: {
            collectionName,
            database: mongoDatabase,
            name: "default",
            mappings: searchIndexMappings,
            analyzers: searchIndexAnalyzers,
          },
        },
      );

    console.log("createIndexResponse");
    console.log(createIndexResponse);
    console.log(createIndexData.toString());
    return JSON.parse(createIndexData);
  }
};

updateAllSearchIndexes()
  .then((indexes) => {
    console.log(indexes);
    process.exit(0);
  })
  .catch((e) => console.error(e));
