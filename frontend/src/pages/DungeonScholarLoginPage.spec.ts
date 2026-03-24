import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";
import { ROUTES } from "../constants/routes";
import { i18n } from "../i18n";
import DungeonScholarLoginPage from "./DungeonScholarLoginPage.vue";

const createTestRouter = () =>
  createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: ROUTES.login, component: DungeonScholarLoginPage },
      { path: ROUTES.signUp, component: DungeonScholarLoginPage },
    ],
  });

describe("DungeonScholarLoginPage", () => {
  it("renders login form with social icons and core inputs", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.login);
    await router.isReady();

    const wrapper = mount(DungeonScholarLoginPage, {
      global: { plugins: [router, i18n] },
    });

    expect(wrapper.find('input[type="email"]').exists()).toBe(true);
    expect(wrapper.find('input[type="password"]').exists()).toBe(true);
    expect(wrapper.findAll('input[type="password"]')).toHaveLength(1);

    const providerIcons = wrapper.findAll(".social-buttons__icon img");
    expect(providerIcons).toHaveLength(3);
    expect(providerIcons[0].attributes("src")).toContain("/login-assets/icon-google.svg");
  });

  it("renders sign-up variant with extra fields", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.signUp);
    await router.isReady();

    const wrapper = mount(DungeonScholarLoginPage, {
      global: { plugins: [router, i18n] },
    });

    expect(wrapper.text()).toContain("Create");
    expect(wrapper.find('input[type="text"]').exists()).toBe(true);
    expect(wrapper.findAll('input[type="password"]')).toHaveLength(2);
  });

  it("shows language menu when clicking translation icon", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.login);
    await router.isReady();

    const wrapper = mount(DungeonScholarLoginPage, {
      global: { plugins: [router, i18n] },
    });

    expect(wrapper.find(".language-dock__menu").exists()).toBe(false);
    await wrapper.get(".language-dock__trigger").trigger("click");

    expect(wrapper.find(".language-dock__menu").exists()).toBe(true);
    expect(wrapper.findAll(".language-dock__option").length).toBeGreaterThanOrEqual(3);
  });
});
