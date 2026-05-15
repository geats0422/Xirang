import { describe, expect, it, vi } from "vitest";
import { ref } from "vue";
import { createSoundEffects } from "./useSoundEffects";

describe("useSoundEffects", () => {
  it("does not play when sound is disabled", () => {
    const playTone = vi.fn();
    const sound = createSoundEffects(ref(false), playTone);

    sound.playCorrect();
    sound.playWrong();
    sound.playSettlement();

    expect(playTone).not.toHaveBeenCalled();
  });

  it("plays distinct cues when sound is enabled", () => {
    const playTone = vi.fn();
    const sound = createSoundEffects(ref(true), playTone);

    sound.playCorrect();
    sound.playWrong();
    sound.playSettlement();

    expect(playTone).toHaveBeenCalledWith([523, 659], 0.08, 0.05);
    expect(playTone).toHaveBeenCalledWith([196, 146], 0.1, 0.045);
    expect(playTone).toHaveBeenCalledWith([392, 523, 784], 0.12, 0.045);
  });
});
