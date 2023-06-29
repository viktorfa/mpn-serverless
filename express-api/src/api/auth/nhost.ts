import * as jose from "jose";
import { getBearerToken, getCognitoIdentityId } from "./utils";
import { Request, Response, NextFunction } from "express";
import ApiError from "@/api/utils/APIError";

type NhostToken = {
  "https://hasura.io/jwt/claims": {
    "x-hasura-Org-Id": string;
    "x-hasura-Org-Ids": string;
    "x-hasura-Org-User-Id": string;
    "x-hasura-allowed-roles": ["me", "user_with_inherit", "user", "admin"];
    "x-hasura-default-role": "user_with_inherit";
    "x-hasura-user-id": string;
    "x-hasura-user-is-anonymous": "false" | "true";
  };
  sub: string;
  iat: number;
  exp: number;
  iss: "hasura-auth";
};

const canBypassAuthentication = (req: Request) => {
  if (["GET", "OPTIONS", "HEAD"].includes(req.method)) {
    return true;
  } else if (req.method === "POST" && req.path.startsWith("/v1/reviews")) {
    return true;
  } else if (
    req.method === "POST" &&
    req.path === "/v1/offers" &&
    !!getCognitoIdentityId(req)
  ) {
    return true;
  } else if (process.env.NODE_ENV !== "production") {
    return true;
  }
  return false;
};

export default async (req: Request, res: Response, next: NextFunction) => {
  const jwtKey: string = process.env.NHOST_JWT_SECRET;
  if (canBypassAuthentication(req)) {
    const bearerToken = getBearerToken(req);
    if (bearerToken) {
      try {
        await jose.jwtVerify(bearerToken, new TextEncoder().encode(jwtKey));
        const decodedToken = jose.decodeJwt(bearerToken) as NhostToken;
        req["user"] = decodedToken;
      } catch (error) {
        res
          .status(403)
          .json({ error: 403, message: error.message, code: error.code })
          .end();
      }
    }
    next();
  } else {
    const cognitoIdentityId = getCognitoIdentityId(req);
    if (req.method === "POST" && /\/offers\/?$/.test(req.path)) {
      if (!!cognitoIdentityId) {
        next();
      }
    }
    const bearerToken = getBearerToken(req);
    if (!bearerToken) {
      return res
        .status(400)
        .json({ status: 403, message: "No Authorization header" })
        .end();
    }
    try {
      await jose.jwtVerify(bearerToken, new TextEncoder().encode(jwtKey));
      const decodedToken = jose.decodeJwt(bearerToken) as NhostToken;
      const userId =
        decodedToken["https://hasura.io/jwt/claims"]["x-hasura-user-id"];
      if (userId) {
        req["user"] = userId;
      } else {
        throw new ApiError({
          message: "User cannot be anonymous",
          status: 401,
        });
      }
      req["user"] = decodedToken;
    } catch (error) {
      res.status(403).json({ error: 403, message: error.message }).end();
    }
    next();
  }
};
