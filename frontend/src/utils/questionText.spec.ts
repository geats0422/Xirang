import { describe, expect, it } from "vitest";

import { stripQuestionFormatting } from "./questionText";

describe("stripQuestionFormatting", () => {
  it("removes common markdown wrappers from question text", () => {
    const input = "**核心转变**：从最初试图同时覆盖 `建筑` 与 _教育_";

    expect(stripQuestionFormatting(input)).toBe("核心转变：从最初试图同时覆盖 建筑 与 教育");
  });

  it("removes heading/list/quote prefixes and keeps plain words", () => {
    const input = `# 标题
- [选项](https://example.com)
> 结论`;

    expect(stripQuestionFormatting(input)).toBe("标题 选项 结论");
  });
});
