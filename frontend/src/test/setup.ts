import { config } from "@vue/test-utils";
import { beforeEach } from "vitest";
import { i18n } from "../i18n";

const plugins = config.global.plugins ?? [];

if (!plugins.includes(i18n)) {
  config.global.plugins = [...plugins, i18n];
}

beforeEach(() => {
  i18n.global.locale.value = "en";
  document.documentElement.lang = "en";
  delete document.documentElement.dataset.theme;
});
