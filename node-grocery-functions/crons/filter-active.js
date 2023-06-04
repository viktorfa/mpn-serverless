const { getCollection } = require("../config/mongo");

const flagInactiveOffers = async () => {
  const cutoffDate = new Date();

  console.time("flagInactiveOffers");
  const collection = await getCollection("mpnoffers");
  const updateResponse = await collection.updateMany(
    { validThrough: { $lt: cutoffDate }, isRecent: { $ne: false } },
    { $set: { isRecent: false } },
  );

  collection.close();
  console.timeEnd("flagInactiveOffers");

  console.log("updateResponse");
  console.log(updateResponse.result);
  return updateResponse.result;
};

module.exports = {
  flagInactiveOffers,
};
