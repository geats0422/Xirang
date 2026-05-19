import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";
import { i18n } from "../i18n";
import DungeonScholarHelpCenterPage from "./DungeonScholarHelpCenterPage.vue";
import DungeonScholarPrivacyPolicyPage from "./DungeonScholarPrivacyPolicyPage.vue";
import DungeonScholarTermsPage from "./DungeonScholarTermsPage.vue";

const supportEmail = "support@xiranglearn.quest";
const automatedEmail = "noreply@xiranglearn.quest";

const createTestRouter = () =>
  createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/help-center", component: DungeonScholarHelpCenterPage },
      { path: "/privacy-policy", component: DungeonScholarPrivacyPolicyPage },
      { path: "/terms-of-service", component: DungeonScholarTermsPage },
    ],
  });

describe("legal and help contact email", () => {
  it.each([
    ["/help-center", DungeonScholarHelpCenterPage],
    ["/privacy-policy", DungeonScholarPrivacyPolicyPage],
    ["/terms-of-service", DungeonScholarTermsPage],
  ])("shows support email on %s", async (path, component) => {
    const router = createTestRouter();
    await router.push(path);
    await router.isReady();

    const wrapper = mount(component, { global: { plugins: [i18n, router] } });

    expect(wrapper.text()).toContain(supportEmail);
    expect(wrapper.text()).not.toContain(automatedEmail);
  });

  it("renders terms content without missing i18n keys", async () => {
    const router = createTestRouter();
    await router.push("/terms-of-service");
    await router.isReady();

    const wrapper = mount(DungeonScholarTermsPage, { global: { plugins: [i18n, router] } });

    expect(wrapper.text()).not.toContain("termsOfService.section4_1Item3");
    expect(wrapper.text()).not.toContain("termsOfService.section6Item3");
  });

  it("keeps legal age and support response promises consistent", async () => {
    i18n.global.locale.value = "en";
    const router = createTestRouter();
    await router.push("/terms-of-service");
    await router.isReady();

    const terms = mount(DungeonScholarTermsPage, { global: { plugins: [i18n, router] } });
    const privacy = mount(DungeonScholarPrivacyPolicyPage, { global: { plugins: [i18n, router] } });

    expect(terms.text()).toContain("You must be at least 14 years old");
    expect(privacy.text()).toContain("We do not allow minors under 14");
    expect(terms.text()).toContain("2 business days");
    expect(terms.text()).not.toContain("30 business days");
  });
});
