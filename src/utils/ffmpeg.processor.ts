import ffmpeg from 'fluent-ffmpeg';
import { randomUUID } from 'node:crypto';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';

export type VoiceProfile =
  | 'baby'
  | 'girl'
  | 'boy'
  | 'deep_man'
  | 'helium'
  | 'robot'
  | 'monster'
  | 'radio'
  | 'echo'
  | 'underwater'
  | 'chipmunk';

export interface VoiceTransformResult {
  outputPath: string;
  mimeType: 'audio/ogg';
  codec: 'libopus';
  profile: VoiceProfile;
}

const SAMPLE_RATE = 44_100;

export const voiceProfileFilters: Readonly<Record<VoiceProfile, readonly string[]>> = {
  baby: [`asetrate=${SAMPLE_RATE}*1.4`, `aresample=${SAMPLE_RATE}`, 'atempo=0.7142857143', 'equalizer=f=3500:t=q:w=1:g=3'],
  girl: [`asetrate=${SAMPLE_RATE}*1.3`, `aresample=${SAMPLE_RATE}`, 'atempo=0.7692307692', 'equalizer=f=2800:t=q:w=1:g=2'],
  boy: [`asetrate=${SAMPLE_RATE}*1.15`, `aresample=${SAMPLE_RATE}`, 'atempo=0.8695652174', 'equalizer=f=1800:t=q:w=1:g=1.5'],
  deep_man: [`asetrate=${SAMPLE_RATE}*0.75`, `aresample=${SAMPLE_RATE}`, 'atempo=1.3333333333', 'lowpass=f=3600', 'equalizer=f=140:t=q:w=1:g=5'],
  helium: [`asetrate=${SAMPLE_RATE}*1.8`, `aresample=${SAMPLE_RATE}`, 'atempo=0.5555555556', 'highpass=f=250'],
  robot: ['aecho=0.8:0.88:6:0.4', 'flanger=delay=8:depth=6:regen=55:width=75:speed=0.5:shape=sinusoidal', 'afftfilt=real=re*sin(0.8):imag=im*cos(0.8)'],
  monster: [`asetrate=${SAMPLE_RATE}*0.62`, `aresample=${SAMPLE_RATE}`, 'atempo=1.6129032258', 'tremolo=f=10:d=0.7', 'acrusher=level_in=1.6:level_out=0.8:bits=7:mode=log'],
  radio: ['highpass=f=1000', 'lowpass=f=3000', 'acompressor=threshold=-18dB:ratio=4:attack=5:release=50', 'volume=1.4'],
  echo: ['aecho=0.8:0.9:1000:0.3', 'aecho=0.6:0.5:500:0.2'],
  underwater: ['lowpass=f=400', 'aecho=0.7:0.45:120:0.25', 'volume=0.9'],
  chipmunk: [`asetrate=${SAMPLE_RATE}*1.5`, `aresample=${SAMPLE_RATE}`, 'atempo=1.5', 'highpass=f=300'],
};

const outputDirectory = path.resolve(process.cwd(), 'tmp', 'voice-transforms');

export function isVoiceProfile(value: string): value is VoiceProfile {
  return Object.hasOwn(voiceProfileFilters, value);
}

export function parseVoiceProfile(value: string | undefined): VoiceProfile {
  if (value !== undefined && isVoiceProfile(value)) {
    return value;
  }
  return 'girl';
}

export async function processVoiceToOggOpus(inputPath: string, requestedProfile: string | undefined): Promise<VoiceTransformResult> {
  const profile = parseVoiceProfile(requestedProfile);
  await mkdir(outputDirectory, { recursive: true });
  const outputPath = path.join(outputDirectory, `${randomUUID()}-${profile}.ogg`);

  await new Promise<void>((resolve, reject) => {
    ffmpeg(inputPath)
      .audioFilters([...voiceProfileFilters[profile]])
      .audioCodec('libopus')
      .format('ogg')
      .outputOptions(['-application voip', '-b:a 48k', '-vbr on', '-compression_level 10'])
      .on('end', resolve)
      .on('error', reject)
      .save(outputPath);
  });

  return { outputPath, mimeType: 'audio/ogg', codec: 'libopus', profile };
}
