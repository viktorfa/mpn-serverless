import { getBearerToken, getCognitoIdentityId } from "./utils";
import { Request, Response, NextFunction } from "express";
import CognitoExpress from "cognito-express";

const cognitoExpress = new CognitoExpress({
  region: "eu-central-1",
  cognitoUserPoolId: "eu-central-1_Enkl9UjC8",
  tokenUse: "access", //Possible Values: access | id
  tokenExpiration: 3600000, //Up to default expiration of 1 hour (3600000 ms)
});

export default async (req: Request, res: Response, next: NextFunction) => {
  const cognitoAccessToken = getCognitoIdentityId(req);
  if (!cognitoAccessToken) {
    return res.status(401).send();
  }
  try {
    const cognitoExpressResponse = await cognitoExpress.validate(
      cognitoAccessToken,
    );
    req["user"] = cognitoExpressResponse;
    next();
  } catch {
    return res.status(401).send();
  }
};
