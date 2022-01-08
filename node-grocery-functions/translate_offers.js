const { Translate } = require("@google-cloud/translate").v2;
const { TranslationServiceClient } = require("@google-cloud/translate");
const { getCollection } = require("./config/mongo");

const translateOffer = async (offer) => {
  return offer;
};

const projectId = "mpnmpn";
const keyFilename = "credentials/_SECRET_mpnmpn-0999db534665.json";
const location = "global";

const targetLanguage = "fi";
const targetMarket = "fi";
const targetTld = "fi";
const targetTag = "";
const targetSiteCollection = "fibyggoffers";

const run = async () => {
  const translate = new Translate({ projectId, keyFilename });
  const translationServiceClient = new TranslationServiceClient({
    projectId,
    keyFilename,
  });
  const offerCollection = await getCollection("mpnoffers");

  const offers = await offerCollection
    .find({
      dealer: "amazon_se",
      href: { $ne: null },
      ahref: { $ne: null },
      provenance: "amazon_se_bygg_api_spider",
    })
    .sort({ pageviews: -1 })
    .limit(200)
    .skip(200)
    .toArray();

  console.log(`Offers: ${offers.length}`);

  const titles = offers.map((x) => x.title);
  const [translationResponse] = await translationServiceClient.translateText({
    parent: `projects/${projectId}/locations/${location}`,
    contents: titles,
    mimeType: "text/plain",
    sourceLanguageCode: "sv",
    targetLanguageCode: targetLanguage,
  });
  //const translatedTitles = await translate.translate(titles, "no");

  console.log(JSON.stringify(titles, null, 2));
  console.log(JSON.stringify(translationResponse.translations, null, 2));

  const translatedOffers = [];
  offers.forEach((offer, i) => {
    const uri = offer.uri.replace("amazon_se", `amazon_${targetMarket}`);
    const dealer = offer.dealer.replace("amazon_se", `amazon_${targetMarket}`);
    const href = offer.href
      .replace("amazon.se", `amazon.${targetTld}`)
      .replace("mpn00e-21", targetTag);
    const ahref = offer.ahref
      .replace("amazon.se", `amazon.${targetTld}`)
      .replace("mpn00e-21", targetTag);
    translatedOffers.push({
      ...offer,
      title: translationResponse.translations[i].translatedText,
      description: "",
      market: targetMarket,
      uri,
      href,
      ahref,
      dealer,
      siteCollection: targetSiteCollection,
      validThrough: new Date("2021-12-31"),
    });
    delete translatedOffers[i]._id;
  });

  const amazonOfferCollection = await getCollection("amazon_offers");

  const bulkWriteResult = await amazonOfferCollection.bulkWrite(
    translatedOffers.map((offer) => {
      return {
        updateOne: {
          filter: { uri: offer.uri },
          update: { $set: offer },
          upsert: true,
        },
      };
    }),
    { ordered: false },
  );

  console.log(bulkWriteResult);

  offerCollection.close();
};

run();
