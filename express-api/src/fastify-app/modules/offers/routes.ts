import {
  type FastifyReply,
  type FastifyRequest,
  type FastifyInstance,
  type FastifyPluginOptions,
} from "fastify";
import { Static, Type } from "@sinclair/typebox";
import { getPricingHandler, getPricingSchema } from "./prices";
import { getUri } from "./utils";
import {
  priceDifferencesHandler,
  priceDifferencesSchema,
} from "./price-differences";
import { searchRelationsHandler, searchRelationsSchema } from "./browse";
import { getSingleHandler, getSingleSchema } from "./single";
import { extraRelationsHandler, extraRelationsSchema } from "./extra";

export const offerRoutes = async (
  server: FastifyInstance,
  options: FastifyPluginOptions,
) => {
  server.get("/:uri/pricing", getPricingSchema, (request, reply) =>
    getPricingHandler(request, reply, server),
  );

  server.get("/searchrelations", searchRelationsSchema, (request, reply) =>
    searchRelationsHandler(request, reply, server),
  );

  const singleRedirectSchema = {
    schema: {
      params: Type.Object({
        uri: Type.String(),
      }),
      response: {
        200: Type.Object({
          href: Type.String(),
          ahref: Type.Optional(Type.String()),
          title: Type.String(),
        }),
        404: Type.Object({
          error: Type.String(),
        }),
      },
    },
  };
  const singleRedirectHandler = async (
    request: FastifyRequest<{
      Params: Static<typeof singleRedirectSchema.schema.params>;
    }>,
    reply: FastifyReply,
  ): Promise<Static<(typeof singleRedirectSchema.schema.response)["200"]>> => {
    const uri = getUri(request.params.uri);

    const offer = await server.db
      .selectFrom("offers")
      .select(["href", "ahref", "title"])
      .where("uri", "=", uri)
      .executeTakeFirst();

    if (!offer) {
      return reply.code(404).send({ error: "Not found" });
    }

    return reply.code(200).send(offer);
  };
  server.get("/:uri/redirect", singleRedirectSchema, singleRedirectHandler);

  server.get("/extrarelations/:uri", extraRelationsSchema, (request, reply) =>
    extraRelationsHandler(request, reply, server),
  );

  server.get("/pricedifferences", priceDifferencesSchema, (request, reply) =>
    priceDifferencesHandler(request, reply, server),
  );

  server.get("/:uri", getSingleSchema, (request, reply) =>
    getSingleHandler(request, reply, server),
  );
};
