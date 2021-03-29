module.exports = () => {
  return {
    stage: process.env.NODE_ENV === "production" ? "prod" : "dev",
    logRetentionInDays: process.env.NODE_ENV === "production" ? 30 : 1,
  };
};
