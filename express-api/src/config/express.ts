import express from "express";
import morgan from "morgan";
import bodyParser from "body-parser";
import cors from "cors";

import routes from "@/api/routes/v1";

const app = express();
app.use(cors());
app.use(morgan("tiny"));
app.use(bodyParser.json());

app.use("/v1", routes);

export default app;
