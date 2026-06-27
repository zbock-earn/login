import type { Request, Response } from 'express';
import { transformVoice } from '../audioutils/ffmpegVoiceProcessor.js';

export async function transformVoiceController(req: Request, res: Response) {
  if (!req.file) return res.status(400).json({ error: 'Missing audio file field named audio' });
  const outputPath = await transformVoice(req.file.path, String(req.query.voiceProfile ?? 'girl'));
  res.type('audio/ogg').download(outputPath);
}
