import urllib from "urllib";
import { mongoDatabase } from "../config/vars";

const searchIndexMappings = {
  dynamic: false,
  fields: {
    brandKey: {
      analyzer: "lucene.keyword",
      indexOptions: "docs",
      norms: "omit",
      searchAnalyzer: "lucene.keyword",
      store: false,
      type: "string",
    },
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
    difference7DaysMeanPercentage: {
      type: "number",
    },
    difference90DaysMeanPercentage: {
      type: "number",
    },
    isPartner: {
      type: "boolean",
    },
    market: {
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
      },
      type: "document",
    },
    pageviews: {
      indexDoubles: false,
      representation: "int64",
      type: "number",
    },
    pricing: {
      fields: {
        price: {
          type: "number",
        },
      },
      type: "document",
    },
    siteCollection: {
      analyzer: "lucene.keyword",
      indexOptions: "docs",
      norms: "omit",
      searchAnalyzer: "lucene.keyword",
      store: false,
      type: "string",
    },
    validThrough: {
      type: "date",
    },
    value: {
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
    vendorKey: {
      analyzer: "lucene.keyword",
      norms: "omit",
      searchAnalyzer: "lucene.keyword",
      store: false,
      type: "string",
    },
  },
};

const searchIndexAnalyzers = [
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
  "mpnoffers_au",
  "mpnoffers_de",
  "mpnoffers_dk",
  "mpnoffers_es",
  "mpnoffers_fi",
  "mpnoffers_fr",
  "mpnoffers_it",
  "mpnoffers_nl",
  "mpnoffers_no",
  "mpnoffers_pl",
  "mpnoffers_se",
  "mpnoffers_sg",
  "mpnoffers_th",
  "mpnoffers_uk",
  "mpnoffers_us",
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
