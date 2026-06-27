import ffmpeg from 'fluent-ffmpeg';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';
import { randomUUID } from 'node:crypto';
import { assertVoiceProfile, voiceFilters, type VoiceProfile } from './voiceProfiles.js';

const outputDir = path.resolve(process.cwd(), 'tmp', 'voice-transforms');

export async function transformVoice(inputPath: string, profile: string) {
  assertVoiceProfile(profile);
  await mkdir(outputDir, { recursive: true });
  const outputPath = path.join(outputDir, `${randomUUID()}-${profile}.ogg`);
  await new Promise<void>((resolve, reject) => {
    ffmpeg(inputPath)
      .audioFilters(voiceFilters[profile as VoiceProfile])
      .audioCodec('libopus')
      .format('ogg')
      .outputOptions(['-application voip', '-b:a 48k', '-vbr on'])
      .save(outputPath)
      .on('end', () => resolve())
      .on('error', reject);
  });
  return outputPath;
}
