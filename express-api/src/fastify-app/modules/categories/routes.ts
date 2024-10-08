import {
  type FastifyReply,
  type FastifyRequest,
  type FastifyInstance,
  type FastifyPluginOptions,
} from "fastify";
import { Static, Type } from "@sinclair/typebox";

export const categoryRoutes = async (
  server: FastifyInstance,
  options: FastifyPluginOptions,
) => {
  const getListSchema = {
    schema: {
      querystring: Type.Object({
        level: Type.Integer(),
        context: Type.String(),
      }),

      response: {
        200: Type.Array(
          Type.Object(
            {
              name: Type.String(),
              key: Type.String(),
              parent: Type.String(),
              level: Type.Integer(),
              context: Type.String(),
              text: Type.String(),
              description: Type.String(),
              active: Type.Boolean(),
            },
            { additionalProperties: true },
          ),
        ),
        404: Type.Object({
          error: Type.String(),
        }),
      },
    },
  };
  const getListHandler = async (
    request: FastifyRequest<{
      Querystring: Static<typeof getListSchema.schema.querystring>;
    }>,
    reply: FastifyReply,
  ): Promise<Static<(typeof getListSchema.schema.response)["200"]>> => {
    const categories = await server.db
      .selectFrom("categories")
      .select([
        "active",
        "context",
        "description",
        "key",
        "level",
        "parent",
        "title",
      ])
      .where("context", "=", request.query.context)
      .where("level", "=", request.query.level)
      .execute();

    const result = categories.map((category) => ({
      name: category.title,
      key: category.key,
      parent: category.parent,
      level: category.level,
      context: category.context,
      text: category.title,
      description: category.description,
      active: category.active,
    }));
    return reply.status(200).send(result);
  };
  server.get("/", getListSchema, getListHandler);

  const getSingleSchema = {
    schema: {
      params: Type.Object({
        categoryKey: Type.String(),
      }),
      querystring: Type.Object({
        context: Type.String(),
      }),
      response: {
        200: Type.Object(
          {
            children: Type.Array(
              Type.Object({}, { additionalProperties: true }),
            ),
          },
          { additionalProperties: true },
        ),
        404: Type.Object({
          error: Type.String(),
        }),
      },
    },
  };

  const getSingleHandler = async (
    request: FastifyRequest<{
      Params: Static<typeof getSingleSchema.schema.params>;
      Querystring: Static<typeof getSingleSchema.schema.querystring>;
    }>,
    reply: FastifyReply,
  ): Promise<Static<(typeof getSingleSchema.schema.response)["200"]>> => {
    const categoryQuery = server.db
      .selectFrom("categories")
      .select([
        "active",
        "context",
        "description",
        "key",
        "level",
        "parent",
        "title",
      ])
      .where("key", "=", request.params.categoryKey)
      .where("context", "=", request.query.context);

    const childrenQuery = server.db
      .selectFrom("categories")
      .select([
        "active",
        "context",
        "description",
        "key",
        "level",
        "parent",
        "title",
      ])
      .where("parent", "=", request.params.categoryKey)
      .where("context", "=", request.query.context);

    const [category, children] = await Promise.all([
      categoryQuery.executeTakeFirst(),
      childrenQuery.execute(),
    ]);

    if (!category) {
      return reply.status(404).send({ error: "Category not found" });
    }

    const childrenFormatted = children.map((child) => ({
      name: child.title,
      key: child.key,
      parent: child.parent,
      level: child.level,
      context: child.context,
      text: child.title,
      description: child.description,
      active: child.active,
    }));

    return reply.status(200).send({
      name: category.title,
      key: category.key,
      parent: category.parent,
      level: category.level,
      context: category.context,
      text: category.title,
      description: category.description,
      active: category.active,
      children: childrenFormatted,
    });
  };

  server.get("/:categoryKey", getSingleSchema, getSingleHandler);
};
