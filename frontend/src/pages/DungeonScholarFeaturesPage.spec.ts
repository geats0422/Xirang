import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";
import { ROUTES } from "../constants/routes";
import { i18n } from "../i18n";
import DungeonScholarFeaturesPage from "./DungeonScholarFeaturesPage.vue";

const discordInviteUrl = "https://discord.gg/tN8CZGAcdM";

const createTestRouter = () =>
  createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: ROUTES.landing, component: { template: "<div>Home</div>" } },
      { path: ROUTES.login, component: { template: "<div>Login</div>" } },
      { path: ROUTES.signUp, component: { template: "<div>Sign Up</div>" } },
      { path: ROUTES.home, component: { template: "<div>App Home</div>" } },
      { path: ROUTES.features, component: DungeonScholarFeaturesPage },
      { path: ROUTES.pricing, component: { template: "<div>Pricing</div>" } },
    ],
  });

describe("DungeonScholarFeaturesPage", () => {
  it("renders a real Discord community link without placeholder footer links", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.features);
    await router.isReady();

    const wrapper = mount(DungeonScholarFeaturesPage, {
      global: { plugins: [router, i18n] },
    });

    expect(wrapper.findAll('a[href="#"]')).toHaveLength(0);
    expect(wrapper.find(`.site-footer__links a[href="${discordInviteUrl}"]`).exists()).toBe(true);
  });
});
