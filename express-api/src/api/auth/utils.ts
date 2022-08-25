import { Request } from "express";

export const getBearerToken = (req: Request) => {
  const bearerToken = req.headers.authorization as string;
  if (!bearerToken) {
    return false;
  }
  const [scheme, idToken] = bearerToken.split(" ");
  if (scheme !== "Bearer" || !idToken) {
    return false;
  }
  return idToken;
};
export const getCognitoIdentityId = (req: Request) => {
  const cognitoToken = req.headers.authorization as string;
  if (!cognitoToken) {
    return false;
  }
  const [scheme, idToken] = cognitoToken.split(" ");
  if (scheme !== "Cognito" || !idToken) {
    return false;
  }
  return idToken;
};
