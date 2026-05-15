import type { Ref } from "vue";
import { useScholarData } from "./useScholarData";

type PlayTone = (frequencies: number[], durationSeconds: number, gainValue: number) => void;

type SoundEffects = {
  playCorrect: () => void;
  playWrong: () => void;
  playSettlement: () => void;
};

let audioContext: AudioContext | null = null;

const getAudioContext = (): AudioContext | null => {
  if (typeof window === "undefined") {
    return null;
  }

  if (!audioContext) {
    audioContext = new AudioContext();
  }

  if (audioContext.state === "suspended") {
    void audioContext.resume();
  }

  return audioContext;
};

const playGeneratedTone: PlayTone = (frequencies, durationSeconds, gainValue) => {
  const context = getAudioContext();
  if (!context) {
    return;
  }

  const now = context.currentTime;
  frequencies.forEach((frequency, index) => {
    const startAt = now + index * durationSeconds * 0.7;
    const oscillator = context.createOscillator();
    const gain = context.createGain();

    oscillator.type = "sine";
    oscillator.frequency.setValueAtTime(frequency, startAt);
    gain.gain.setValueAtTime(0.0001, startAt);
    gain.gain.exponentialRampToValueAtTime(gainValue, startAt + 0.01);
    gain.gain.exponentialRampToValueAtTime(0.0001, startAt + durationSeconds);

    oscillator.connect(gain);
    gain.connect(context.destination);
    oscillator.start(startAt);
    oscillator.stop(startAt + durationSeconds + 0.02);
  });
};

export const createSoundEffects = (
  soundEnabled: Ref<boolean>,
  playTone: PlayTone = playGeneratedTone,
): SoundEffects => {
  const playIfEnabled = (frequencies: number[], durationSeconds: number, gainValue: number) => {
    if (!soundEnabled.value) {
      return;
    }

    playTone(frequencies, durationSeconds, gainValue);
  };

  return {
    playCorrect: () => playIfEnabled([523, 659], 0.08, 0.05),
    playWrong: () => playIfEnabled([196, 146], 0.1, 0.045),
    playSettlement: () => playIfEnabled([392, 523, 784], 0.12, 0.045),
  };
};

export const useSoundEffects = (): SoundEffects => {
  const { soundEnabled } = useScholarData();
  return createSoundEffects(soundEnabled);
};
