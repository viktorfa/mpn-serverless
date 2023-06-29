import { nanoid } from "nanoid";
import slugify from "slugify";
import { addDays } from "date-fns";

export const makeNewMpnOfferFromPartnerProduct = ({
  partnerProduct,
  partner,
}: {
  partnerProduct: PartnerProduct;
  partner: StorePartner;
}) => {
  const offerId = nanoid();
  const uri = `partner:product:${offerId}`;
  const now = new Date();
  const dealerSlug = slugify(partner.name, {
    lower: true,
    replacement: "_",
    locale: "nb",
  });
  const imageUrl = new URL("https://link.sharizard.com/v1/create");
  imageUrl.searchParams.set("backgroundColor", "#eec643");
  imageUrl.searchParams.set("color", "#111111");
  imageUrl.searchParams.set("title", partner.name);
  imageUrl.searchParams.set("subtitle", partnerProduct.title);

  return {
    pricing: { price: partnerProduct.price },
    title: partnerProduct.title,
    description: partnerProduct.description,
    stockAmount: partnerProduct.stockAmount,
    dealer: dealerSlug,
    uri,
    href: `https://allematpriser.no/shop/partners/${partner._id}`,
    imageUrl: imageUrl.toString(),
    partnerId: partner.cognitoId,
    status: "ACTIVE",
    validThrough: addDays(now, 28),
    isRecent: true,
    validFrom: new Date(),
    siteCollection: "groceryoffers",
    market: "no",
    isPartner: true,
  };
};

export const makeUpdateSetMpnOfferFromPartnerProduct = ({
  partnerProduct,
  partner,
}: {
  partnerProduct: PartnerProduct;
  partner: StorePartner;
}) => {
  const now = new Date();
  const imageUrl = new URL("https://link.sharizard.com/v1/create");
  imageUrl.searchParams.set("backgroundColor", "#eec643");
  imageUrl.searchParams.set("color", "#111111");
  imageUrl.searchParams.set("title", partner.name);
  imageUrl.searchParams.set("subtitle", partnerProduct.title);

  return {
    pricing: { price: partnerProduct.price },
    title: partnerProduct.title,
    description: partnerProduct.description,
    stockAmount: partnerProduct.stockAmount,
    imageUrl: imageUrl.toString(),
    validThrough: addDays(now, 28),
    isRecent: true,
  };
};

export const makePartnerProductFromMpnOffer = ({
  mpnOffer,
}: {
  mpnOffer: MpnMongoOfferPartner;
}) => {
  return {
    _id: mpnOffer._id,
    price: mpnOffer.pricing.price,
    title: mpnOffer.title,
    description: mpnOffer.description,
    stockAmount: mpnOffer.stockAmount,
    status: "ACTIVE",
  };
};
