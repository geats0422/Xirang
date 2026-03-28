import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
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
    });

    await wrapper.get(".settlement-overlay").trigger("click");

    expect(wrapper.emitted("close")).toHaveLength(1);
  });

  it("clicking primary action emits confirm", async () => {
    const wrapper = mount(GameSettlementModal, {
      props: baseProps,
    });

    await wrapper.get(".settlement-cta").trigger("click");

    expect(wrapper.emitted("confirm")).toHaveLength(1);
  });

  it("clicking secondary action emits review", async () => {
    const wrapper = mount(GameSettlementModal, {
      props: baseProps,
    });

    await wrapper.get(".settlement-secondary").trigger("click");

    expect(wrapper.emitted("review")).toHaveLength(1);
  });

  it("disables review action when reviewEnabled is false", async () => {
    const wrapper = mount(GameSettlementModal, {
      props: {
        ...baseProps,
        reviewEnabled: false,
      },
    });

    expect(wrapper.get(".settlement-secondary").attributes("disabled")).toBeDefined();
  });
});
