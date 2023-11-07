const ServerlessClient = require("serverless-postgres");

const client = new ServerlessClient({
  user: process.env.NHOST_DB_USER,
  password: process.env.NHOST_DB_PW,
  database: process.env.NHOST_DB_NAME,
  host: process.env.NHOST_DB_HOST,
});

module.exports = { client };
