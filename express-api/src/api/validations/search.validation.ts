import { Joi } from "express-validation";

export const offerSearchValidation = {
  query: Joi.object({ query: Joi.string().required().min(1) }),
};
