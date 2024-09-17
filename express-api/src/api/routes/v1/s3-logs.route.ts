import { router } from "typera-express";
import { Router } from "express";
import { Response, Route, route } from "typera-express";
import { S3Client, GetObjectCommand } from "@aws-sdk/client-s3";
import { Readable } from "node:stream";

const getS3Client = () => {
  return new S3Client({});
};

function webReadableToNodeReadable(webReadable) {
  const reader = webReadable.getReader();
  return new Readable({
    async read() {
      try {
        const { done, value } = await reader.read();
        if (done) {
          this.push(null);
        } else {
          this.push(value);
        }
      } catch (err) {
        this.destroy(err);
      }
    },
  });
}

const getLogs: Route<
  | Response.Ok<ReadableStream>
  | Response.BadRequest<string>
  | Response.InternalServerError<string>
> = route.get("/:s3UrlString").handler(async (request) => {
  const { s3UrlString } = request.routeParams;

  const s3Url = new URL(decodeURIComponent(s3UrlString));
  const Bucket = s3Url.hostname.split(".")[0];
  const Key = s3Url.pathname.slice(1);

  const s3Client = getS3Client();

  const command = new GetObjectCommand({
    Bucket,
    Key,
  });

  const response = await s3Client.send(command);

  return Response.ok(
    Response.streamingBody(async (outputStream) => {
      const readableStream = response.Body.transformToWebStream();
      const nodeReadableStream = webReadableToNodeReadable(readableStream);
      nodeReadableStream.pipe(outputStream);
    }),
    {
      "Content-Type": response.ContentType,
      "Content-Length": response.ContentLength.toString(),
    },
  );
});

const routes: Router = router(getLogs).handler();

export default routes;
