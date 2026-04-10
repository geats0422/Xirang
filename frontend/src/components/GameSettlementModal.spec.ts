import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { i18n } from "../i18n";
import GameSettlementModal from "./GameSettlementModal.vue";

const baseProps = {
  coinReward: 120,
  goalText: "Keep cultivating daily.",
  modeName: "Knowledge Draft",
  visible: true,
  xpGained: 800,
};

describe("GameSettlementModal", () => {
  it("clicking overlay emits close", async () => {
    const wrapper = mount(GameSettlementModal, {
      props: baseProps,
      global: {
        plugins: [i18n],
      },
    });

    await wrapper.get(".settlement-overlay").trigger("click");

    expect(wrapper.emitted("close")).toHaveLength(1);
  });

  it("clicking primary action emits continueToPath", async () => {
    const wrapper = mount(GameSettlementModal, {
      props: baseProps,
      global: {
        plugins: [i18n],
      },
    });

    await wrapper.get(".settlement-cta").trigger("click");

    expect(wrapper.emitted("continueToPath")).toHaveLength(1);
  });
});
