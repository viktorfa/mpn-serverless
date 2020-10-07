const reverseString = (str) => [...str].reverse().join("");

/**
 *
 * @param {import("@/types").SnsEvent} snsEvent
 * @returns {object}
 */
const getMessageFromSnsEvent = (snsEvent) => {
  return JSON.parse(snsEvent.Records[0].Sns.Message);
};

module.exports = {
  reverseString,
  getMessageFromSnsEvent,
};
