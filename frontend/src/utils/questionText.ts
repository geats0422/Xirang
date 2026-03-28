const INLINE_FORMAT_MARKERS = /\*\*|__|~~|`/g;
const INLINE_SINGLE_MARKERS = /(^|[\s(["'])[*_]|[*_](?=[\s)\]"'.,!?;:，。！？；：]|$)/g;

const stripLinePrefix = (value: string): string =>
  value
    .replace(/^\s{0,3}#{1,6}\s+/u, "")
    .replace(/^\s{0,3}>\s?/u, "")
    .replace(/^\s{0,3}(?:[-+*]|\d+\.)\s+/u, "");

export const stripQuestionFormatting = (input: string): string => {
  if (!input.trim()) {
    return "";
  }

  const withoutLinks = input.replace(/\[([^\]]+)\]\(([^)]+)\)/g, "$1");
  const normalizedBreaks = withoutLinks.split(String.fromCharCode(13)).join("");

  const normalizedLines = normalizedBreaks
    .split(String.fromCharCode(10))
    .map((line) => stripLinePrefix(line).replace(INLINE_FORMAT_MARKERS, ""))
    .map((line) => line.replace(INLINE_SINGLE_MARKERS, "$1"))
    .map((line) => line.trim())
    .filter((line) => line.length > 0);

  return normalizedLines.join(" ").replace(/\s{2,}/g, " ").trim();
};
