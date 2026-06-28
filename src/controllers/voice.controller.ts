import type { Request, Response } from 'express';
import type { BaileysManager } from '../services/baileys.manager.js';
import { processVoiceToOggOpus } from '../utils/ffmpeg.processor.js';

interface VoiceTransformQuery {
  voiceProfile?: string;
  jid?: string;
  accountId?: string;
  send?: string;
}

function readQuery(req: Request): VoiceTransformQuery {
  return {
    voiceProfile: typeof req.query.voiceProfile === 'string' ? req.query.voiceProfile : undefined,
    jid: typeof req.query.jid === 'string' ? req.query.jid : undefined,
    accountId: typeof req.query.accountId === 'string' ? req.query.accountId : undefined,
    send: typeof req.query.send === 'string' ? req.query.send : undefined,
  };
}

export class VoiceController {
  constructor(private readonly manager: BaileysManager) {}

  transform = async (req: Request, res: Response): Promise<void> => {
    if (!req.file) {
      res.status(400).json({ error: 'Missing multipart audio file field named audio' });
      return;
    }

    const query = readQuery(req);
    const transformed = await processVoiceToOggOpus(req.file.path, query.voiceProfile);

    if (query.send === 'true') {
      if (!query.accountId || !query.jid) {
        res.status(400).json({ error: 'accountId and jid are required when send=true' });
        return;
      }

      const socket = this.manager.getClient(query.accountId);
      if (!socket) {
        res.status(409).json({ error: 'WhatsApp account is not connected' });
        return;
      }

      await socket.sendMessage(query.jid, {
        audio: { url: transformed.outputPath },
        mimetype: 'audio/mp4',
        ptt: true,
      });
    }

    res.type(transformed.mimeType).download(transformed.outputPath);
  };
}
