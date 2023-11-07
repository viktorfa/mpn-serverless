const fs = require("fs");
const path = require("path");
const jwt = require("jsonwebtoken");
const Handlebars = require("handlebars");
const { client: pgClient } = require("../config/postgres");

const handle = async (event) => {
  console.log("event");
  console.log(event);

  try {
    const { token } = event.queryStringParameters;
    const decodedToken = jwt.verify(token, process.env.JWT_SECRET);
    console.log("decodedToken");
    console.log(decodedToken);

    await pgClient.connect();

    const deleteNotsResponse = await pgClient.query(
      `
        UPDATE public.tracking_offers SET active_status = 'INACTIVE' WHERE org_user = $1
    ;`,
      [decodedToken.sub],
    );

    console.log("deleteNotsResponse");
    console.log(JSON.stringify(deleteNotsResponse, null, 2));

    const handlebarsTemplate = Handlebars.compile(
      fs.readFileSync(path.join(__dirname, "unsubscribed.hbs"), "utf8"),
    );

    return {
      statusCode: 200,
      body: handlebarsTemplate({ lang: "no" }),
      headers: { "Content-Type": "text/html" },
    };
  } catch (e) {
    console.error(e);
    const handlebarsTemplate = Handlebars.compile(
      fs.readFileSync(path.join(__dirname, "error-unsubscribed.hbs"), "utf8"),
    );
    return {
      statusCode: 200,
      body: handlebarsTemplate({ lang: "no", message: e.message }),
      headers: { "Content-Type": "text/html" },
    };
  } finally {
    await pgClient.clean();
  }
};

module.exports = { handle };
