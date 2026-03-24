/**
 * Run Tests Tool
 *
 * Custom OpenCode tool to run test suites with various options.
 * Automatically detects the package manager and test framework.
 */

import { tool } from "@opencode-ai/plugin/tool"

export default tool({
  description:
    "Run the test suite with optional coverage, watch mode, or specific test patterns. Automatically detects package manager (npm, pnpm, yarn, bun) and test framework.",
  args: {
    pattern: tool.schema
      .string()
      .optional()
      .describe("Test file pattern or specific test name to run"),
    coverage: tool.schema
      .boolean()
      .optional()
      .describe("Run with coverage reporting (default: false)"),
    watch: tool.schema
      .boolean()
      .optional()
      .describe("Run in watch mode for continuous testing (default: false)"),
    updateSnapshots: tool.schema
      .boolean()
      .optional()
      .describe("Update Jest/Vitest snapshots (default: false)"),
  },
  async execute(args: Record<string, unknown>, context: { worktree?: string; directory: string; $: any }) {
    const pattern = args.pattern as string | undefined
    const coverage = args.coverage as boolean | undefined
    const watch = args.watch as boolean | undefined
    const updateSnapshots = args.updateSnapshots as boolean | undefined
    const cwd = context.worktree || context.directory
    const $ = context.$

    const packageManager = await detectPackageManager(cwd, $)
    const testFramework = await detectTestFramework(cwd, $)

    let cmd: string[] = [packageManager]

    if (packageManager === "npm") {
      cmd.push("run", "test")
    } else {
      cmd.push("test")
    }

    const testArgs: string[] = []

    if (coverage) {
      testArgs.push("--coverage")
    }

    if (watch) {
      testArgs.push("--watch")
    }

    if (updateSnapshots) {
      testArgs.push("-u")
    }

    if (pattern) {
      if (testFramework === "jest" || testFramework === "vitest") {
        testArgs.push("--testPathPattern", pattern)
      } else {
        testArgs.push(pattern)
      }
    }

    if (testArgs.length > 0) {
      if (packageManager === "npm") {
        cmd.push("--")
      }
      cmd.push(...testArgs)
    }

    const command = cmd.join(" ")

    return JSON.stringify({
      command,
      packageManager,
      testFramework,
      options: {
        pattern: pattern || "all tests",
        coverage: coverage || false,
        watch: watch || false,
        updateSnapshots: updateSnapshots || false,
      },
      instructions: `Run this command to execute tests:\n\n${command}`,
    })
  },
})

async function detectPackageManager(cwd: string, $: any): Promise<string> {
  const lockFiles = [
    { file: "bun.lockb", pm: "bun" },
    { file: "pnpm-lock.yaml", pm: "pnpm" },
    { file: "yarn.lock", pm: "yarn" },
    { file: "package-lock.json", pm: "npm" },
  ]

  for (const { file, pm } of lockFiles) {
    try {
      await $`test -f ${cwd}/${file}`
      return pm
    } catch {
      continue
    }
  }

  return "npm"
}

async function detectTestFramework(cwd: string, $: any): Promise<string> {
  const packageJsonPath = `${cwd}/package.json`

  try {
    await $`test -f ${packageJsonPath}`
    const result = await $`cat ${packageJsonPath}`.catch(() => "")
    const packageJson = JSON.parse(result.toString())
    const deps = {
      ...packageJson.dependencies,
      ...packageJson.devDependencies,
    }

    if (deps.vitest) return "vitest"
    if (deps.jest) return "jest"
    if (deps.mocha) return "mocha"
    if (deps.ava) return "ava"
    if (deps.tap) return "tap"
  } catch {
    // Ignore errors
  }

  return "unknown"
}
