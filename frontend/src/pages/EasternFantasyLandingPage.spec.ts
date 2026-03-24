import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";
import { ROUTES } from "../constants/routes";
import { i18n } from "../i18n";
import EasternFantasyLandingPage from "./EasternFantasyLandingPage.vue";

const createTestRouter = () =>
  createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: ROUTES.landing, component: EasternFantasyLandingPage },
      { path: ROUTES.login, component: { template: "<div>Login</div>" } },
      { path: ROUTES.signUp, component: { template: "<div>Sign Up</div>" } },
      { path: ROUTES.home, component: { template: "<div>Home</div>" } },
    ],
  });

describe("EasternFantasyLandingPage", () => {
  it("renders login action in header", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.landing);
    await router.isReady();

    const wrapper = mount(EasternFantasyLandingPage, {
      global: { plugins: [router, i18n] },
    });

    const ctaButtons = wrapper.findAll(".site-header .cta-route-btn");
    expect(ctaButtons).toHaveLength(2);
    expect(ctaButtons[0].text()).toContain("Login");
    expect(ctaButtons[1].text()).toContain("Sign Up");
  });

  it("navigates to sign-up when clicking register button", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.landing);
    await router.isReady();

    const wrapper = mount(EasternFantasyLandingPage, {
      global: { plugins: [router, i18n] },
    });

    const ctaButtons = wrapper.findAll(".site-header .cta-route-btn");
    await ctaButtons[1].trigger("click");
    await new Promise<void>((resolve) => {
      window.setTimeout(() => resolve(), 260);
    });

    expect(router.currentRoute.value.path).toBe(ROUTES.signUp);
  });

  it("shows top navigation entries", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.landing);
    await router.isReady();

    const wrapper = mount(EasternFantasyLandingPage, {
      global: { plugins: [router, i18n] },
    });

    const navLinks = wrapper.findAll(".site-nav a");
    expect(navLinks.length).toBe(3);
  });
});
