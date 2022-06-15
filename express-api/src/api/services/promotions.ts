import { getCollection } from "@/config/mongo";
import { $fetch } from "ohmyfetch";
import { shuffle } from "lodash";

const adTractionChannels = [
  { market: "no", channelId: "1532500727", productCollection: "byggoffers" },
  { market: "no", channelId: "1532500672", productCollection: "groceryoffers" },
  { market: "no", channelId: "1593949181", productCollection: "beautyoffers" },
  {
    market: "de",
    channelId: "1650547786",
    productCollection: "degroceryoffers",
  },
  {
    market: "se",
    channelId: "1573089698",
    productCollection: "sebyggoffers",
  },
  {
    market: "se",
    channelId: "1573089692",
    productCollection: "segroceryoffers",
  },
  {
    market: "dk",
    channelId: "1685097684",
    productCollection: "dkgroceryoffers",
  },
  {
    market: "dk",
    channelId: "1685097411",
    productCollection: "dkbyggoffers",
  },
];

const adTractionDealers = [
  { key: "kitchentime_se", programId: "1073119263" },
  { key: "lampegiganten", programId: "1493664803" },
  { key: "gardenstore_no", programId: "1331156692" },
  { key: "bangerhead_no", programId: "1663367545" },
  { key: "blush_no", programId: "1650705922" },

  { key: "staples_se", programId: "1338983658" },
  { key: "www.hemkop.se", programId: "1479128951" },
  { key: "granngarden_se", programId: "1080727981" },
  { key: "lamp24", programId: "1493662657" },
  { key: "lampgallerian", programId: "1499748017" },
  { key: "matsmart", programId: "1136290807" },
  { key: "kitchentime_se", programId: "1073119263" },

  { key: "vinoseleccion_de", programId: "1615926092" },
];

export const getAdTractionCampaigns = async ({
  market,
  productCollection,
}: {
  market: string;
  productCollection?: string;
}): Promise<PromotionBanner[]> => {
  let adTractionChannel = adTractionChannels.find(
    (x) => x.productCollection === productCollection,
  );
  if (!adTractionChannel) {
    adTractionChannel = adTractionChannels.find((x) => x.market === market);
  }
  if (!adTractionChannel) {
    return [];
  }
  const body: { market: string; channelId?: string } = {
    market: market.toUpperCase(),
    channelId: adTractionChannel.channelId,
  };
  let campaigns: AdTractionCampaign[] = await $fetch(
    "https://api.adtraction.com/v2/partner/offers/",
    {
      method: "POST",
      headers: {
        "X-Token": "1D044AD28E1178A8820F77258353F98A5E0AECBF",
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body,
    },
  );
  if (!Array.isArray(campaigns)) {
    return [];
  }
  campaigns = shuffle(campaigns);

  const dealerProgramIds = adTractionDealers.map((x) => x.programId);
  const adtractionCampaign = campaigns.find(
    (x) => x.trackingURL && dealerProgramIds.includes(x.programId.toString()),
  );
  if (!adtractionCampaign) {
    return [];
  }
  const dealer = adTractionDealers.find(
    (x) => x.programId === adtractionCampaign.programId.toString(),
  );
  let dealerObject: MpnDealer | null = null;
  if (dealer) {
    const dealerCollection = await getCollection("dealers");
    dealerObject = await dealerCollection.findOne({
      key: dealer.key,
    });
  }
  const result: PromotionBanner = {
    url: adtractionCampaign.trackingURL,
    image: "",
    type: "horizontal",
    text: adtractionCampaign.offerDescription,
  };
  if (dealerObject && dealerObject.logoUrl) {
    result.image = dealerObject.logoUrl;
  } else {
    return [];
  }
  return [result];
};
