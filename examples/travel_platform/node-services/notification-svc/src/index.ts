import express from "express";

import { notifyRouter } from "./routes/notify";
import { startQueueWorker } from "./queue/worker";

const app = express();
app.use(express.json());
app.use("/notify", notifyRouter);

app.get("/healthz", (_, res) => res.json({ status: "ok" }));

startQueueWorker();

const port = Number(process.env.PORT ?? 8081);
app.listen(port, () => console.log(`notification-svc on ${port}`));
