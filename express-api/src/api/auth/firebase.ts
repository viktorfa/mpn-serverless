import { getBearerToken, getCognitoIdentityId } from "./utils";
import firebaseAdmin from "firebase-admin";
import { Request, Response, NextFunction } from "express";
import ApiError from "@/api/utils/APIError";

import { auth } from "firebase-admin";

let firebaseAuth;

const getFirebaseAuth = () => {
  if (!firebaseAuth) {
    firebaseAdmin.initializeApp({
      databaseURL: "https://grocery-prices.firebaseio.com",
      projectId: "grocery-prices",
      storageBucket: "grocery-prices.appspot.com",
    });
    firebaseAuth = firebaseAdmin.auth();
  }
  return firebaseAuth;
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
  if (canBypassAuthentication(req)) {
    const bearerToken = getBearerToken(req);
    if (bearerToken) {
      try {
        const decodedToken: auth.DecodedIdToken =
          await getFirebaseAuth().verifyIdToken(bearerToken);
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
      const decodedToken: auth.DecodedIdToken =
        await getFirebaseAuth().verifyIdToken(bearerToken);
      if (decodedToken.email) {
        req["user"] = decodedToken;
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
