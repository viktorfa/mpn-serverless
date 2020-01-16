const getTokens = (string) => string.split(" ");
const getBigrams = (tokens) => {
  if (!tokens || tokens.length < 2) return [];
  const result = [];
  tokens.forEach((token, index, arr) => {
    if (arr.length > index + 1) {
      result.push(`${token} ${arr[index + 1]}`);
    }
  });
  return result;
};

const preprocessHeading = (string) => {
  let result = string || "";
  result = result.toLowerCase();
  result = result.trim();
  result = result.replace(/[.,]/gu, " ");
  result = result.replace(/ {2,}/gu, " ");
  return result;
};

module.exports = {
  getBigrams,
  getTokens,
  preprocessHeading,
};
