import { ofetch } from "ofetch";
import * as t from "io-ts";
import { Response, Route, route, Parser } from "typera-express";

const channelIdMap = {
  "1650547786": {
    context: "amp-de",
    measurement_id: "G-KKLRH24BQ0",
    api_secret: "pg0QDXlPRo-qCAFY_12l-g",
  },
  "1573089698": {
    context: "bygg-se",
    measurement_id: "G-V6PERVM9LT",
    api_secret: "w9acJOotTcKte7b4RILgQg",
  },
  "1573089692": {
    context: "amp-se",
    measurement_id: "G-7BD1TX350D",
    api_secret: "CENT47d7TCGFDB-_XC_Pnw",
  },
  "1532500727": {
    context: "bygg-no",
    measurement_id: "G-RB2CNJF49B",
    api_secret: "9xi8CBiIQKu86h1kd8PPFw",
  },
  "1685097684": {
    context: "amp-dk",
    measurement_id: "G-ECEZGE74CQ",
    api_secret: "Q2WrjxvlQuiOEE_B_3FnWg",
  },
  "1685097411": {
    context: "bygg-dk",
    measurement_id: "G-WVM6KSEEY3",
    api_secret: "ILQLmRwOQtu10NQDgZpGYQ",
  },
  "1532500672": {
    context: "amp-no",
    measurement_id: "G-Q075N4YKPV",
    api_secret: "8Old2-yoR-ehSuV8EjYuNg",
  },
  "1593949181": {
    context: "beauty-no",
    measurement_id: "G-SZ3YXNQ93B",
    api_secret: "PZAbai1VTrO-TjNNlglD_g",
  },
};

const adtractionQueryParams = t.type({
  cid: t.union([t.string, t.undefined]),
  channelid: t.union([t.string, t.undefined]),
  commission: t.union([t.string, t.undefined]),
  currency: t.union([t.string, t.undefined]),
  programname: t.union([t.string, t.undefined]),
  uniqueid: t.union([t.string, t.undefined]),
  transactionname: t.union([t.string, t.undefined]),
  actiondate: t.union([t.string, t.undefined]),
});

export const adTractionPurchase: Route<
  | Response.Ok<undefined>
  | Response.BadRequest<string>
  | Response.InternalServerError<string>
> = route
  .use(Parser.query(adtractionQueryParams))
  .get("/adtraction")
  .handler(async (request) => {
    const { measurement_id, api_secret } =
      channelIdMap[request.query.channelid];
    try {
      const googleAnalResponse = await ofetch(
        `https://www.google-analytics.com/mp/collect`,
        {
          method: "POST",
          query: {
            measurement_id,
            api_secret,
          },
          body: {
            client_id: request.query.cid,
            timestamp_micros: request.query.actiondate + "000000",
            events: [
              {
                name: "purchase",
                params: {
                  currency: request.query.currency,
                  value: Number.parseInt(request.query.commission) / 100,
                  transaction_id: request.query.uniqueid,
                  items: [
                    {
                      item_id: request.query.programname,
                      item_name: request.query.transactionname,
                    },
                  ],
                },
              },
            ],
          },
        },
      );
      return Response.ok(googleAnalResponse);
    } catch (e) {
      console.error(e);
      console.error(e.message);
      console.error(e.data);
      return Response.internalServerError(e.data);
    }
  });
