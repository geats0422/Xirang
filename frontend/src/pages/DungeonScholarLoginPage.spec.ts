import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import DungeonScholarLoginPage from "./DungeonScholarLoginPage.vue";

describe("DungeonScholarLoginPage", () => {
  it("renders email/password form with local static assets", () => {
    const wrapper = mount(DungeonScholarLoginPage);

    expect(wrapper.find('input[type="email"]').exists()).toBe(true);
    expect(wrapper.find('input[type="password"]').exists()).toBe(true);

    const providerIcons = wrapper.findAll(".social-buttons__icon img");
    expect(providerIcons).toHaveLength(3);
    expect(providerIcons[0].attributes("src")).toContain("/login-assets/icon-google.svg");
  });
});
