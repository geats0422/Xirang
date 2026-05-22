import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createMemoryHistory, createRouter } from "vue-router";
import { ROUTES } from "../constants/routes";
import { i18n } from "../i18n";
import DungeonScholarLoginPage from "./DungeonScholarLoginPage.vue";

const { registerWithPasswordMock, sendRegistrationVerificationCodeMock, wakeupServerMock } = vi.hoisted(() => ({
  registerWithPasswordMock: vi.fn(),
  sendRegistrationVerificationCodeMock: vi.fn(),
  wakeupServerMock: vi.fn(),
}));

vi.mock("../api/auth", async () => {
  const actual = await vi.importActual<typeof import("../api/auth")>("../api/auth");
  return {
    ...actual,
    sendRegistrationVerificationCode: sendRegistrationVerificationCodeMock,
    registerWithPassword: registerWithPasswordMock,
  };
});

vi.mock("../api/wakeup", () => ({
  wakeupServer: wakeupServerMock,
}));

const createTestRouter = () =>
  createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: ROUTES.login, component: DungeonScholarLoginPage },
      { path: ROUTES.signUp, component: DungeonScholarLoginPage },
    ],
  });

describe("DungeonScholarLoginPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sendRegistrationVerificationCodeMock.mockResolvedValue({
      ok: true,
      expires_in_seconds: 600,
      resend_after_seconds: 60,
    });
    registerWithPasswordMock.mockResolvedValue({
      user: { id: "user-1", username: "Hero", email: "hero@example.com", status: "active" },
      tokens: {
        access_token: "access-token",
        refresh_token: "refresh-token",
        token_type: "bearer",
        expires_in: 900,
      },
    });
    wakeupServerMock.mockResolvedValue(undefined);
  });

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
    expect(wrapper.find('input[inputmode="numeric"]').exists()).toBe(true);
    expect(wrapper.findAll('input[type="password"]')).toHaveLength(2);
  });

  it("sends a registration verification code for the entered email", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.signUp);
    await router.isReady();

    const wrapper = mount(DungeonScholarLoginPage, {
      global: { plugins: [router, i18n] },
    });

    await wrapper.get('input[type="email"]').setValue("Hero@Example.com");
    await wrapper.get(".email-form__send-code").trigger("click");

    expect(sendRegistrationVerificationCodeMock).toHaveBeenCalledWith({
      email: "hero@example.com",
    });
    expect(wrapper.text()).toContain("Code sent");
  });

  it("submits sign-up with the entered verification code", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.signUp);
    await router.isReady();

    const wrapper = mount(DungeonScholarLoginPage, {
      global: { plugins: [router, i18n] },
    });

    await wrapper.get('input[type="text"]').setValue("Hero");
    await wrapper.get('input[type="email"]').setValue("Hero@Example.com");
    await wrapper.findAll('input[type="password"]')[0].setValue("Secret-pass1!");
    await wrapper.findAll('input[type="password"]')[1].setValue("Secret-pass1!");
    await wrapper.get('input[inputmode="numeric"]').setValue("123456");
    await wrapper.get("form").trigger("submit");

    expect(registerWithPasswordMock).toHaveBeenCalledWith({
      username: "Hero",
      email: "hero@example.com",
      password: "Secret-pass1!",
      verificationCode: "123456",
    });
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

  it("starts Google OAuth immediately even when server wakeup is still pending", async () => {
    const router = createTestRouter();
    await router.push(ROUTES.signUp);
    await router.isReady();
    wakeupServerMock.mockReturnValue(new Promise(() => undefined));

    const wrapper = mount(DungeonScholarLoginPage, {
      global: { plugins: [router, i18n] },
    });

    await wrapper.findAll(".social-buttons__item")[0].trigger("click");

    expect(wrapper.findAll(".social-buttons__item")[0].attributes("disabled")).toBeUndefined();
  });
});
