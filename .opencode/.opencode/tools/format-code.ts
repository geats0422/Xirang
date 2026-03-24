/**
 * Format Code Tool
 *
 * Language-aware code formatter that auto-detects the project's formatter.
 * Supports: Biome/Prettier (JS/TS), Black (Python), gofmt (Go), rustfmt (Rust)
 */

import { tool } from "@opencode-ai/plugin"

export default tool({
  name: "format-code",
  description: "Format a file using the project's configured formatter. Auto-detects Biome, Prettier, Black, gofmt, or rustfmt.",
  args: {
    filePath: tool.schema
      .string()
      .describe("Path to the file to format"),
    formatter: tool.schema
      .string()
      .optional()
      .describe("Override formatter: biome, prettier, black, gofmt, rustfmt (default: auto-detect)"),
  },
  async execute(args: Record<string, unknown>, context: { $: any }) {
    const filePath = args.filePath as string
    const formatterOverride = args.formatter as string | undefined
    const $ = context.$

    const ext = filePath.split(".").pop()?.toLowerCase() || ""

    let detected = formatterOverride
    if (!detected) {
      if (["ts", "tsx", "js", "jsx", "json", "css", "scss"].includes(ext)) {
        try {
          await $`test -f biome.json || test -f biome.jsonc`
          detected = "biome"
        } catch {
          detected = "prettier"
        }
      } else if (["py", "pyi"].includes(ext)) {
        detected = "black"
      } else if (ext === "go") {
        detected = "gofmt"
      } else if (ext === "rs") {
        detected = "rustfmt"
      }
    }

    if (!detected) {
      return JSON.stringify({ formatted: false, message: `No formatter detected for .${ext} files` })
    }

    const commands: Record<string, string> = {
      biome: `npx @biomejs/biome format --write ${filePath}`,
      prettier: `npx prettier --write ${filePath}`,
      black: `black ${filePath}`,
      gofmt: `gofmt -w ${filePath}`,
      rustfmt: `rustfmt ${filePath}`,
    }

    const cmd = commands[detected]
    if (!cmd) {
      return JSON.stringify({ formatted: false, message: `Unknown formatter: ${detected}` })
    }

    try {
      const result = await $`${cmd}`.text()
      return JSON.stringify({ formatted: true, formatter: detected, output: result })
    } catch (error: unknown) {
      const err = error as { stderr?: string }
      return JSON.stringify({ formatted: false, formatter: detected, error: err.stderr || "Format failed" })
    }
  },
})
