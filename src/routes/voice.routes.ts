import { randomUUID } from 'node:crypto';
import path from 'node:path';
import { Router } from 'express';
import multer from 'multer';
import type { BaileysManager } from '../services/baileys.manager.js';
import { VoiceController } from '../controllers/voice.controller.js';

export function buildVoiceRoutes(manager: BaileysManager): Router {
  const router = Router();
  const storage = multer.diskStorage({
    destination: path.resolve(process.cwd(), 'tmp', 'uploads'),
    filename: (_request, file, callback) => callback(null, `${randomUUID()}-${file.originalname}`),
  });
  const upload = multer({ storage });
  const controller = new VoiceController(manager);

  router.post('/transform', upload.single('audio'), controller.transform);

  return router;
}
