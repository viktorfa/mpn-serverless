import { Joi } from "express-validation";

export const echoValidation = {
  params: Joi.object({ message: Joi.string().required().min(2) }),
};
