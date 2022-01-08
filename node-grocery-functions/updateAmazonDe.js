const { getCollection } = require("./config/mongo");
const fs = require("fs");
const _ = require("lodash");

const updateAmazonDe = async () => {
  const now = new Date();
  const offerCollection = await getCollection("mpnoffers");
  const amazonDeOffers = await offerCollection
    .find({ dealer: "amazon_de" })
    .project({ href: 1, uri: 1 })
    .toArray();

  const updates = amazonDeOffers.map((offer) => {
    /**@var string */
    let href = offer.href;
    if (href.includes("?")) {
      href = href.replace(/\?.+/, "");
    }
    const ahref = `${href}?tag=mpn06e-21`;

    return {
      updateOne: { filter: { uri: offer.uri }, update: { $set: { ahref } } },
    };
  });
  const result = await offerCollection.bulkWrite(updates);
  offerCollection.close();

  console.log("FINISH");
  console.log(JSON.stringify(result));
};

updateAmazonDe();
