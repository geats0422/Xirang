<script setup lang="ts">
import DOMPurify from "dompurify";
import hljs from "highlight.js/lib/core";
import bash from "highlight.js/lib/languages/bash";
import javascript from "highlight.js/lib/languages/javascript";
import json from "highlight.js/lib/languages/json";
import python from "highlight.js/lib/languages/python";
import typescript from "highlight.js/lib/languages/typescript";
import MarkdownIt from "markdown-it";
import { computed } from "vue";

type MarkdownRenderer = InstanceType<typeof MarkdownIt>;

hljs.registerLanguage("bash", bash);
hljs.registerLanguage("javascript", javascript);
hljs.registerLanguage("json", json);
hljs.registerLanguage("python", python);
hljs.registerLanguage("typescript", typescript);

const markdown: MarkdownRenderer = new MarkdownIt({
  breaks: true,
  html: false,
  linkify: true,
  typographer: true,
  highlight(code: string, language: string) {
    const normalized = language.trim().toLowerCase();

    if (normalized && hljs.getLanguage(normalized)) {
      try {
        return `<pre><code class="hljs language-${normalized}">${hljs.highlight(code, { language: normalized }).value}</code></pre>`;
      } catch {
        // fallback to escaped block
      }
    }

    return `<pre><code class="hljs">${markdown.utils.escapeHtml(code)}</code></pre>`;
  },
});

const sanitizeOptions = {
  USE_PROFILES: { html: true },
  ADD_ATTR: ["target", "rel"],
  ALLOW_DATA_ATTR: false,
  FORBID_TAGS: ["style", "script", "iframe", "form", "input", "textarea", "button", "select"],
};

const addSecureAnchorAttributes = (html: string): string => {
  if (typeof window === "undefined" || typeof DOMParser === "undefined") {
    return html;
  }

  const parser = new DOMParser();
  const documentFragment = parser.parseFromString(html, "text/html");
  const anchors = documentFragment.querySelectorAll("a");
  anchors.forEach((anchor) => {
    anchor.setAttribute("target", "_blank");
    anchor.setAttribute("rel", "noopener noreferrer nofollow");
  });
  return documentFragment.body.innerHTML;
};

const props = withDefaults(
  defineProps<{
    content?: string | null;
    inline?: boolean;
    className?: string;
  }>(),
  {
    content: "",
    inline: false,
    className: "",
  },
);

const classes = computed(() => [
  "markdown-rich-text",
  props.inline ? "markdown-rich-text--inline" : "",
  props.className,
]);

const renderedHtml = computed(() => {
  const source = props.content ?? "";
  if (!source) {
    return "";
  }

  try {
    const html = props.inline ? markdown.renderInline(source) : markdown.render(source);
    const sanitized = DOMPurify.sanitize(html, sanitizeOptions);
    return addSecureAnchorAttributes(sanitized);
  } catch {
    return markdown.utils.escapeHtml(source);
  }
});
</script>

<template>
  <!-- eslint-disable-next-line vue/no-v-html -->
  <span v-if="inline" :class="classes" v-html="renderedHtml" />
  <!-- eslint-disable-next-line vue/no-v-html -->
  <div v-else :class="classes" v-html="renderedHtml" />
</template>
