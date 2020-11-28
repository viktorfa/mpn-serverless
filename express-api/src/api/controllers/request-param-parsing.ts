export const getStringList = (commaSeparatedList: string): string[] =>
  commaSeparatedList.split(",");

export const getBoolean = (param: string): boolean =>
  ["1", "true"].includes(param);
