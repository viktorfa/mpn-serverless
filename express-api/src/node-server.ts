import app from "@/config/express";
import { port } from "@/config/vars";

app.listen(port, () => {
  console.log(`⚡️[server]: Server is running at ${port || 3000}`);
});
