/**
 * Lint Check Tool
 *
 * Multi-language linter that auto-detects the project's linting tool.
 * Supports: ESLint/Biome (JS/TS), Pylint/Ruff (Python), golangci-lint (Go)
 */

import { tool } from "@opencode-ai/plugin"

export default tool({
  name: "lint-check",
  description: "Run linter on files or directories. Auto-detects ESLint, Biome, Ruff, Pylint, or golangci-lint.",
  args: {
    target: tool.schema
      .string()
      .optional()
      .describe("File or directory to lint (default: current directory)"),
    fix: tool.schema
      .boolean()
      .optional()
      .describe("Auto-fix issues if supported (default: false)"),
    linter: tool.schema
      .string()
      .optional()
      .describe("Override linter: eslint, biome, ruff, pylint, golangci-lint (default: auto-detect)"),
  },
  async execute(args: Record<string, unknown>, context: { $: any }) {
    const target = (args.target as string) || "."
    const fix = (args.fix as boolean) || false
    const linterOverride = args.linter as string | undefined
    const $ = context.$

    let detected = linterOverride
    if (!detected) {
      try {
        await $`test -f biome.json || test -f biome.jsonc`
        detected = "biome"
      } catch {
        try {
          await $`test -f .eslintrc.json || test -f .eslintrc.js || test -f .eslintrc.cjs || test -f eslint.config.js || test -f eslint.config.mjs`
          detected = "eslint"
        } catch {
          try {
            await $`test -f pyproject.toml && grep -q "ruff" pyproject.toml`
            detected = "ruff"
          } catch {
            try {
              await $`test -f .golangci.yml || test -f .golangci.yaml`
              detected = "golangci-lint"
            } catch {
              detected = "eslint"
            }
          }
        }
      }
    }

    const commands: Record<string, string> = {
      biome: `npx @biomejs/biome lint${fix ? " --write" : ""} ${target}`,
      eslint: `npx eslint${fix ? " --fix" : ""} ${target}`,
      ruff: `ruff check${fix ? " --fix" : ""} ${target}`,
      pylint: `pylint ${target}`,
      "golangci-lint": `golangci-lint run${fix ? " --fix" : ""} ${target}`,
    }

    const cmd = commands[detected || "eslint"]
    if (!cmd) {
      return JSON.stringify({ success: false, message: `Unknown linter: ${detected}` })
    }

    try {
      const result = await $`${cmd}`.text()
      return JSON.stringify({ success: true, linter: detected, output: result, issues: 0 })
    } catch (error: unknown) {
      const err = error as { stdout?: string; stderr?: string }
      return JSON.stringify({
        success: false,
        linter: detected,
        output: err.stdout || "",
        errors: err.stderr || "",
      })
    }
  },
})
