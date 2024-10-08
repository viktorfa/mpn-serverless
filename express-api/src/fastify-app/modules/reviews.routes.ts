import {
  type FastifyReply,
  type FastifyRequest,
  type FastifyInstance,
  type FastifyPluginOptions,
} from "fastify";
import { Static, Type } from "@sinclair/typebox";

export const reviewRoutes = async (
  server: FastifyInstance,
  options: FastifyPluginOptions,
) => {
  const getForOfferSchema = {
    schema: {
      params: Type.Object({
        uri: Type.String(),
      }),

      response: {
        200: Type.Array(Type.Object({}, { additionalProperties: true })),
        404: Type.Object({
          error: Type.String(),
        }),
      },
    },
  };
  const getForOfferHandler = async (
    request: FastifyRequest<{
      Params: Static<typeof getForOfferSchema.schema.params>;
    }>,
    reply: FastifyReply,
  ): Promise<Static<(typeof getForOfferSchema.schema.response)["200"]>> => {
    return reply.code(200).send([]);
  };
  server.get("/:uri", getForOfferSchema, getForOfferHandler);
};
