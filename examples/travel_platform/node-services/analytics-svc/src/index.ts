import express from "express";

import { ingestRouter } from "./ingest/router";

const app = express();
app.use(express.json());
app.use("/ingest", ingestRouter);

app.get("/healthz", (_, res) => res.json({ status: "ok" }));

const port = Number(process.env.PORT ?? 8082);
app.listen(port, () => console.log(`analytics-svc on ${port}`));
