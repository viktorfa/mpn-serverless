const mongoIdRegexPattern = /^[0-9a-fA-F]{24}$/;

export const isMongoUri = (str: string) => !!str.match(mongoIdRegexPattern);

/**
 * Gets a "rounded" date that is now rounded to the last whole hour.
 * Because this can be useful when caching queries.
 */
export const getNowDate = (): Date => {
  const now = new Date();
  now.setMilliseconds(0);
  now.setSeconds(0);
  now.setMinutes(0);
  return now;
};
export const getDaysAhead = (days: number): Date => {
  const result = new Date();
  result.setDate(result.getDate() + days);
  return result;
};
