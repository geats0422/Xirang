import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import MarkdownRichText from "./MarkdownRichText.vue";

describe("MarkdownRichText", () => {
  it("renders bold syntax", () => {
    const wrapper = mount(MarkdownRichText, {
      props: {
        content: "hello **world**",
      },
    });

    expect(wrapper.html()).toContain("<strong>world</strong>");
  });

  it("sanitizes dangerous attributes", () => {
    const wrapper = mount(MarkdownRichText, {
      props: {
        content: '<img src="x" onerror="alert(1)">',
      },
    });

    expect(wrapper.find("img").exists()).toBe(false);
    expect(wrapper.html()).toContain("&lt;img");
  });

  it("renders fenced code blocks", () => {
    const wrapper = mount(MarkdownRichText, {
      props: {
        content: "```ts\nconst answer = 42;\n```",
      },
    });

    expect(wrapper.find("pre code").exists()).toBe(true);
    expect(wrapper.html()).toContain("language-ts");
  });

  it("adds secure attributes for links", () => {
    const wrapper = mount(MarkdownRichText, {
      props: {
        content: "[Open](https://example.com)",
      },
    });

    const anchor = wrapper.find("a");
    expect(anchor.attributes("target")).toBe("_blank");
    expect(anchor.attributes("rel")).toContain("noopener");
  });

  it("supports inline rendering mode", () => {
    const wrapper = mount(MarkdownRichText, {
      props: {
        content: "`inline`",
        inline: true,
      },
    });

    expect(wrapper.html()).toContain("markdown-rich-text--inline");
    expect(wrapper.find("code").exists()).toBe(true);
  });
});
