const { NhostClient } = require("@nhost/nhost-js");
const gql = require("graphql-tag");
const { uniqBy, capitalize } = require("lodash");
const { getCollection } = require("../config/mongo");
const { getMessageFromSnsEvent } = require("../utils");

/**
 *
 * @param {import("@/types").SnsEvent<import("@/types").OfferFeedHandledMessage>} event
 */
const handlerSns = async (event) => {
  console.log("event");
  console.log(event);
  console.log(JSON.stringify(event, null, 2));
  /** @type {import("@/types").OfferFeedHandledMessage} */
  const snsMessage = getMessageFromSnsEvent(event);
  const { scrapeBatchId } = snsMessage;

  if (!scrapeBatchId) {
    throw new Error("No scrapeBatchId");
  }

  return handleOffers(snsMessage);
};
/**
 *
 * @param {import("@/types").OfferFeedHandledMessage} event
 */
const handlerTrigger = async (event) => {
  console.log("event");
  console.log(event);
  console.log(JSON.stringify(event, null, 2));
  const { scrapeBatchId } = event;

  return handleOffers(event);
};

/**
 *
 * @param {{scrapeBatchId:string, market:string, is_partner:boolean}} param0
 */
const handleOffers = async ({ scrapeBatchId, market, is_partner }) => {
  const collection = await getCollection("mpnoffers");
  const offers = await collection
    .find({ scrapeBatchId })
    .project({
      dealerKey: 1,
      brandKey: 1,
      vendorKey: 1,
      brand: 1,
      vendor: 1,
    })
    .toArray();

  const dealers = uniqBy(
    offers
      .filter((x) => !!x.dealerKey)
      .map((x) => ({
        key: x.dealerKey,
        title: getDealerTitle(x.dealerKey),
        market,
        is_partner,
      })),
    (x) => x.key + x.market,
  );
  const brands = uniqBy(
    offers
      .filter((x) => !!x.brandKey)
      .map((x) => ({ key: x.brandKey, title: x.brand, market })),
    (x) => x.key + x.market,
  );
  const vendors = uniqBy(
    offers
      .filter((x) => !!x.vendorKey)
      .map((x) => ({ key: x.vendorKey, title: x.vendor, market })),
    (x) => x.key + x.market,
  );

  await collection.close();

  const nhostClient = new NhostClient({
    region: process.env.NHOST_REGION,
    subdomain: process.env.NHOST_SUBDOMAIN,
  });

  const insertResponses = await Promise.all([
    nhostClient.graphql.request(
      gql`
        mutation INSERT_DEALERS($objects: [dealers_insert_input!]!) {
          insert_dealers(
            objects: $objects
            on_conflict: { constraint: dealers_key_market_key }
          ) {
            affected_rows
          }
        }
      `,
      { objects: dealers },
      { headers: { "x-hasura-admin-secret": process.env.NHOST_ADMIN_SECRET } },
    ),
    nhostClient.graphql.request(
      gql`
        mutation INSERT_BRANDS($objects: [brands_insert_input!]!) {
          insert_brands(
            objects: $objects
            on_conflict: { constraint: brands_key_market_key }
          ) {
            affected_rows
          }
        }
      `,
      { objects: brands },
      { headers: { "x-hasura-admin-secret": process.env.NHOST_ADMIN_SECRET } },
    ),
    nhostClient.graphql.request(
      gql`
        mutation INSERT_VENDORS($objects: [vendors_insert_input!]!) {
          insert_vendors(
            objects: $objects
            on_conflict: { constraint: vendors_key_market_key }
          ) {
            affected_rows
          }
        }
      `,
      { objects: vendors },
      { headers: { "x-hasura-admin-secret": process.env.NHOST_ADMIN_SECRET } },
    ),
  ]);

  console.log("insertResponses");
  console.log(insertResponses);
  return insertResponses;
};

module.exports = {
  handlerSns,
  handleOffers,
  handlerTrigger,
};

/**
 *
 * @param {string} dealer
 * @returns {string}
 */
const getDealerTitle = (dealer) => {
  return capitalize(
    dealer
      .replace(/www\./g, "")
      .replace(/_(no|se|de|dk|fi|us|uk|sg|th|nl|fr|es|it|pl|au)$/g, "")
      .replace(/\_/g, " "),
  );
};
