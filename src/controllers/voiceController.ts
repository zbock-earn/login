import type { Request, Response } from 'express';
import { processVoiceToOggOpus } from '../utils/ffmpeg.processor.js';

export async function transformVoiceController(req: Request, res: Response): Promise<void> {
  if (!req.file) {
    res.status(400).json({ error: 'Missing multipart audio file field named audio' });
    return;
  }
  const requestedProfile = typeof req.query.voiceProfile === 'string' ? req.query.voiceProfile : undefined;
  const transformed = await processVoiceToOggOpus(req.file.path, requestedProfile);
  res.type(transformed.mimeType).download(transformed.outputPath);
}
