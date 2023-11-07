const fs = require("fs");
const path = require("path");
const jwt = require("jsonwebtoken");
const Handlebars = require("handlebars");
const { getMessageFromSnsEvent } = require("../utils");
const { getCollection } = require("../config/mongo");
const { groupBy } = require("lodash");
const Ses = require("aws-sdk/clients/ses");
const { client: pgClient } = require("../config/postgres");
const sgMail = require("@sendgrid/mail");

/**
 *
 * @param {import("@/types").SnsEvent<import("@/types").OfferFeedHandledMessage>} event
 */
const handlerSns = async (event) => {
  console.log("event");
  console.log(event);
  console.log(JSON.stringify(event, null, 2));
  /** @type {import("@/types").OfferFeedHandledMessage} */
  const snsMessage = getMessageFromSnsEvent(event);
  const { scrapeBatchId } = snsMessage;

  if (!scrapeBatchId) {
    throw new Error("No scrapeBatchId");
  }

  return handleOffers(snsMessage);
};

/**
 *
 * @param {import("@/types").OfferFeedHandledMessage} event
 */
const handlerTrigger = async (event) => {
  console.log("event");
  console.log(event);
  console.log(JSON.stringify(event, null, 2));

  return handleOffers(event);
};

/**
 *
 * @param {{scrapeBatchId:string, market:string, is_partner:boolean, namespace:string}} param0
 */
const handleOffers = async ({
  scrapeBatchId,
  market,
  is_partner,
  namespace,
}) => {
  if (!scrapeBatchId) {
    throw new Error("No scrapeBatchId");
  }
  console.time("handle offers notifications");
  console.log("process.env.NHOST_DB_HOST", process.env.NHOST_DB_HOST);
  await pgClient.connect();

  try {
    const res = await pgClient.query(
      "SELECT id, uri, gtin, title FROM tracking_offers;",
      [],
    );
    console.timeLog("handle offers notifications", "sql finished");
    console.log(res.rows);
    const uriToNotificationMap = {};
    res.rows.forEach((x) => {
      uriToNotificationMap[x.uri] = x;
    });
    const gtinToNotificationMap = {};
    res.rows
      .filter((x) => !!x)
      .forEach((x) => {
        gtinToNotificationMap[x.gtin] = x;
      });
    const eans = Object.keys(gtinToNotificationMap)
      .filter((x) => x.startsWith("ean"))
      .map((x) => x.split(":")[1]);
    const gtins = Object.keys(gtinToNotificationMap)
      .filter((x) => x.startsWith("gtin"))
      .map((x) => x.split(":")[1]);
    const collection = await getCollection("mpnoffers");
    const offers = await collection
      .find({
        scrapeBatchId,
        $or: [
          { uri: { $in: Object.keys(uriToNotificationMap) } },
          { "gtins.ean": { $in: eans } },
          { "gtins.gtin": { $in: gtins } },
          { "gtins.gtin12": { $in: gtins } },
          { "gtins.gtin13": { $in: gtins } },
        ],
        difference: { $lt: process.env.NODE_ENV === "production" ? 0 : 1 },
      })
      .project({
        title: 1,
        difference: 1,
        differencePercentage: 1,
        gtins: 1,
        uri: 1,
        dealer: 1,
      })
      .toArray();
    collection.close();
    console.timeLog("handle offers notifications", "mongo finished");
    console.log("offers");
    console.log(offers);

    const notifications = [];

    offers.forEach((x) => {
      const notification = uriToNotificationMap[x.uri];
      if (notification) {
        notifications.push({ ...notification, ...x });
      }
      const gtinNotification = gtinToNotificationMap[x.gtins?.ean];
      if (gtinNotification) {
        notifications.push({
          ...gtinNotification,
          ...x,
        });
      }
    });
    console.log("notifications");
    console.log(notifications);

    const notificationMap = {};

    notifications.forEach((x) => {
      notificationMap[x.id] = x;
    });

    const notRes = await pgClient.query(
      `SELECT public.tracking_offers.id, public.tracking_offers.uri, public.tracking_offers.gtin, public.tracking_offers.title, auth.users.email, public.tracking_offers.org_user 
      FROM public.tracking_offers 
      JOIN public.org_users ON public.tracking_offers.org_user = public.org_users.id 
      JOIN auth.users ON public.org_users.user = auth.users.id
      WHERE public.tracking_offers.id = ANY($1) AND public.tracking_offers.active_status = 'ACTIVE' 
      ;`,
      [notifications.map((x) => x.id)],
    );
    console.timeLog("handle offers notifications", "nots with join finished");
    console.log("notRes.rows");
    console.log(notRes.rows);

    if (notRes.rows.length === 0) {
      console.log("No notifications to send");
      return;
    }

    notRes.rows.forEach((x) => {
      const notificationOffer = notificationMap[x.id];
      Object.assign(x, {
        ...x,
        ...notificationMap[x.id],
        url: `https://allematpriser.no/tilbud/${notificationOffer.uri}`,
      });
    });

    console.log("notRes.rows");
    console.log(notRes.rows);

    const groupedNots = groupBy(
      notRes.rows.filter((x) => !!x.email),
      (x) => x.email,
    );

    const handlebarsTemplate = Handlebars.compile(
      fs.readFileSync(path.join(__dirname, "price-drops.hbs"), "utf8"),
    );

    const fromEmail =
      process.env.NODE_ENV === "production"
        ? "info@allematpriser.no"
        : `info-${process.env.NODE_ENV}@allematpriser.no`;

    const sesResponses = await Promise.all(
      Object.entries(groupedNots)
        .filter(([email]) => {
          if (process.env.NODE_ENV === "production") {
            return true;
          } else {
            return email === "vikfand@gmail.com";
          }
        })
        .map(([email, nots]) => {
          const unsubscribeUrl = `${
            process.env.ENDPOINT_URL
          }/unsubscribe?token=${jwt.sign(
            { sub: nots[0].org_user },
            process.env.JWT_SECRET,
            { expiresIn: "180 days" },
          )}`;

          const htmlTemplate = handlebarsTemplate({
            nOffers: nots.length,
            offers: nots.map((x) => ({
              ...x,
              differencePercentage: x.differencePercentage.toFixed(2),
            })),
            lang: "no",
            unsubscribeUrl,
          });

          if (false) {
            return sendWithSes({
              to: email,
              from: fromEmail,
              fromName: "Allematpriser.no",
              html: htmlTemplate,
              subject: `Prisfall på ${nots.length} tilbud`,
            });
          } else {
            return sendWithSendgrid({
              to: email,
              from: fromEmail,
              fromName: "Allematpriser.no",
              html: htmlTemplate,
              subject: `Prisfall på ${nots.length} tilbud`,
            });
          }
        }),
    );
    console.log("sesResponses");
    console.log(JSON.stringify(sesResponses, null, 2));
  } catch (err) {
    console.error(err);
  } finally {
    await pgClient.clean();
    console.timeEnd("handle offers notifications");
  }
};

/**
 *
 * @param {Object} param0
 * @param {string} param0.to
 * @param {string} param0.from
 * @param {string} param0.fromName
 * @param {string} param0.html
 * @param {string=} param0.text
 * @param {string} param0.subject
 * @returns {Promise}
 */
const sendWithSes = async ({ to, from, fromName, html, text, subject }) => {
  const sesClient = new Ses();

  return sesClient
    .sendEmail({
      Destination: {
        ToAddresses: [to],
      },
      Message: {
        Body: {
          Html: {
            Charset: "UTF-8",
            Data: html,
          },
        },
        Subject: {
          Charset: "UTF-8",
          Data: subject,
        },
      },
      Source: `${fromName} <${from}>`,
    })
    .promise();
};

/**
 *
 * @param {Object} param0
 * @param {string} param0.to
 * @param {string} param0.from
 * @param {string} param0.fromName
 * @param {string} param0.html
 * @param {string=} param0.text
 * @param {string} param0.subject
 * @returns {Promise}
 */
const sendWithSendgrid = async ({
  to,
  from,
  fromName,
  html,
  text,
  subject,
}) => {
  sgMail.setApiKey(process.env.SENDGRID_API_KEY);
  return sgMail.send({
    to: to,
    from: { email: from, name: fromName },
    subject: subject,
    text,
    html,
  });
};

module.exports = {
  handlerSns,
  handlerTrigger,
};
