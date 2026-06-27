export type VoiceProfile = 'baby' | 'girl' | 'boy' | 'deep_man' | 'helium' | 'robot' | 'monster' | 'radio' | 'echo' | 'underwater' | 'chipmunk';

export const voiceFilters: Record<VoiceProfile, string[]> = {
  baby: ['asetrate=48000*1.35,aresample=48000,atempo=1.08'],
  girl: ['asetrate=48000*1.22,aresample=48000,atempo=0.98'],
  boy: ['asetrate=48000*1.12,aresample=48000,atempo=1.0'],
  deep_man: ['asetrate=48000*0.78,aresample=48000,atempo=0.94'],
  helium: ['asetrate=48000*1.7,aresample=48000,atempo=1.05'],
  robot: ['afftfilt=real=re*sin(1):imag=im*cos(1)', 'flanger=delay=8:depth=4:regen=60:width=70:speed=0.6'],
  monster: ['asetrate=48000*0.62,aresample=48000,atempo=0.9', 'acrusher=level_in=2:level_out=0.8:bits=8:mode=log'],
  radio: ['highpass=f=1000', 'lowpass=f=3000', 'acompressor=threshold=-18dB:ratio=4:attack=5:release=50'],
  echo: ['aecho=0.8:0.88:60:0.4', 'aecho=0.6:0.5:180:0.25'],
  underwater: ['lowpass=f=400', 'aecho=0.7:0.4:120:0.2'],
  chipmunk: ['asetrate=48000*1.5,aresample=48000,atempo=1.5'],
};

export function assertVoiceProfile(profile: string): asserts profile is VoiceProfile {
  if (!(profile in voiceFilters)) {
    throw new Error(`Unsupported voice profile: ${profile}`);
  }
}
