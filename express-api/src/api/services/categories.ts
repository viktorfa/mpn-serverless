import { getCollection } from "@/config/mongo";
import { ObjectId } from "mongodb";
import { mpnCategoriesCollectionName } from "@/api/utils/constants";

export const findOne = async ({
  id,
  key,
}: {
  id?: string;
  key?: string;
}): Promise<MpnCategory> => {
  const categoriesCollection = await getCollection(mpnCategoriesCollectionName);
  if (id) {
    return categoriesCollection.findOne<MpnCategory>({ _id: new ObjectId(id) });
  } else if (key) {
    return categoriesCollection.findOne<MpnCategory>({ key });
  } else {
    throw new Error("Need uri or id to get category");
  }
};
export const findByKeys = async ({
  keys,
}: {
  keys: string[];
}): Promise<MpnCategory[]> => {
  const categoriesCollection = await getCollection(mpnCategoriesCollectionName);
  return categoriesCollection
    .find<MpnCategory>({ key: { $in: keys } })
    .toArray();
};
