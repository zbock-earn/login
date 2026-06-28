import { Router } from 'express';
import multer from 'multer';
import { randomUUID } from 'node:crypto';
import path from 'node:path';
import type { BaileysManager } from '../services/baileysManager.js';
import { requireTenant } from '../middleware/tenant.js';
import { sessionController } from '../controllers/sessionController.js';
import { listMessages } from '../controllers/messageController.js';
import { buildVoiceRoutes } from './voice.routes.js';

export function buildRoutes(manager: BaileysManager) {
  const router = Router();
  const storage = multer.diskStorage({
    destination: path.resolve(process.cwd(), 'tmp', 'uploads'),
    filename: (_req, file, cb) => cb(null, `${randomUUID()}-${file.originalname}`),
  });
  const upload = multer({ storage });
  const sessions = sessionController(manager);

  router.use(requireTenant);
  router.get('/sessions', sessions.list);
  router.post('/sessions', sessions.create);
  router.post('/sessions/:accountId/connect', sessions.connect);
  router.get('/accounts/:accountId/messages', listMessages);
  router.use('/voice', buildVoiceRoutes(manager));
  router.post('/voice/transform-file-only', upload.single('audio'), async (req, res, next) => {
    const { transformVoiceController } = await import('../controllers/voiceController.js');
    return transformVoiceController(req, res).catch(next);
  });

  return router;
}
