import express from "express";
import morgan from "morgan";
import bodyParser from "body-parser";
import cors from "cors";

import firebaseAuth from "@/api/auth/firebase";
import routes from "@/api/routes/v1";

const app = express();

app.use(cors());
app.use(morgan("tiny"));

app.use(firebaseAuth);

app.use(bodyParser.json());

app.use("/v1", routes);

export default app;
