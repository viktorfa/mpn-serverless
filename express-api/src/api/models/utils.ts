export const getStrippedProductCollectionName = (
  collectionName: string,
): string =>
  collectionName.endsWith("s")
    ? `${collectionName.substring(0, collectionName.length - 1)}`
    : collectionName;
