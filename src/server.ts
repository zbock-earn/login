import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import { createServer } from 'node:http';
import path from 'node:path';
import { Server } from 'socket.io';
import { prisma } from './lib/prisma.js';
import { BaileysManager } from './services/baileysManager.js';
import { registerSocketServer } from './services/socketHub.js';
import { buildRoutes } from './routes/index.js';

const app = express();
const httpServer = createServer(app);
const io = new Server(httpServer, { cors: { origin: process.env.CORS_ORIGIN?.split(',') ?? '*' } });
const manager = new BaileysManager(prisma);

registerSocketServer(io);
app.use(helmet());
app.use(cors({ origin: process.env.CORS_ORIGIN?.split(',') ?? '*' }));
app.use(express.json({ limit: '5mb' }));
app.use(express.static(path.resolve(process.cwd(), 'public')));
app.get('/', (_req, res) => res.sendFile(path.resolve(process.cwd(), 'public', 'index.html')));
app.use('/api', buildRoutes(manager));
app.get('/healthz', (_req, res) => res.json({ ok: true }));

const port = Number(process.env.PORT ?? 3000);
httpServer.listen(port, async () => {
  await manager.bootstrapConnectedAccounts();
  console.log(`WhatsApp SaaS API listening on :${port}`);
});
