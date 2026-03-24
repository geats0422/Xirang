/**
 * Check Coverage Tool
 *
 * Custom OpenCode tool to analyze test coverage and report on gaps.
 * Supports common coverage report formats.
 */

import { tool } from "@opencode-ai/plugin/tool"

export default tool({
  description:
    "Check test coverage against a threshold and identify files with low coverage. Reads coverage reports from common locations.",
  args: {
    threshold: tool.schema
      .number()
      .optional()
      .describe("Minimum coverage percentage required (default: 80)"),
    showUncovered: tool.schema
      .boolean()
      .optional()
      .describe("Show list of uncovered files (default: true)"),
    format: tool.schema
      .enum(["summary", "detailed", "json"])
      .optional()
      .describe("Output format (default: summary)"),
  },
  async execute(args: Record<string, unknown>, context: { worktree?: string; directory: string; $: any }) {
    const threshold = (args.threshold as number) ?? 80
    const showUncovered = (args.showUncovered as boolean) ?? true
    const format = (args.format as string) ?? "summary"
    const cwd = context.worktree || context.directory
    const $ = context.$ as any

    const coveragePaths = [
      "coverage/coverage-summary.json",
      "coverage/lcov-report/index.html",
      "coverage/coverage-final.json",
      ".nyc_output/coverage.json",
    ]

    let coverageData: CoverageSummary | null = null
    let coverageFile: string | null = null

    for (const coveragePath of coveragePaths) {
      const fullPath = `${cwd}/${coveragePath}`
      if (coveragePath.endsWith(".json")) {
        try {
          const result = await $`cat ${fullPath}`.catch(() => "")
          const content = JSON.parse(result.toString())
          coverageData = parseCoverageData(content)
          coverageFile = coveragePath
          break
        } catch {
          // Continue to next file
        }
      }
    }

    if (!coverageData) {
      return JSON.stringify({
        success: false,
        error: "No coverage report found",
        suggestion:
          "Run tests with coverage first: npm test -- --coverage",
        searchedPaths: coveragePaths,
      })
    }

    const passed = coverageData.total.percentage >= threshold
    const uncoveredFiles = coverageData.files.filter(
      (f) => f.percentage < threshold
    )

    const result: CoverageResult = {
      success: passed,
      threshold,
      coverageFile,
      total: coverageData.total,
      passed,
    }

    if (format === "detailed" || (showUncovered && uncoveredFiles.length > 0)) {
      result.uncoveredFiles = uncoveredFiles.slice(0, 20)
      result.uncoveredCount = uncoveredFiles.length
    }

    if (format === "json") {
      result.rawData = coverageData
    }

    if (!passed) {
      result.suggestion = `Coverage is ${coverageData.total.percentage.toFixed(1)}% which is below the ${threshold}% threshold. Focus on these files:\n${uncoveredFiles
        .slice(0, 5)
        .map((f) => `- ${f.file}: ${f.percentage.toFixed(1)}%`)
        .join("\n")}`
    }

    return JSON.stringify(result)
  },
})

interface CoverageSummary {
  total: {
    lines: number
    covered: number
    percentage: number
  }
  files: Array<{
    file: string
    lines: number
    covered: number
    percentage: number
  }>
}

interface CoverageResult {
  success: boolean
  threshold: number
  coverageFile: string | null
  total: CoverageSummary["total"]
  passed: boolean
  uncoveredFiles?: CoverageSummary["files"]
  uncoveredCount?: number
  rawData?: CoverageSummary
  suggestion?: string
}

function parseCoverageData(data: unknown): CoverageSummary {
  if (typeof data === "object" && data !== null && "total" in data) {
    const istanbulData = data as Record<string, unknown>
    const total = istanbulData.total as Record<string, { total: number; covered: number }>

    const files: CoverageSummary["files"] = []

    for (const [key, value] of Object.entries(istanbulData)) {
      if (key !== "total" && typeof value === "object" && value !== null) {
        const fileData = value as Record<string, { total: number; covered: number }>
        if (fileData.lines) {
          files.push({
            file: key,
            lines: fileData.lines.total,
            covered: fileData.lines.covered,
            percentage: fileData.lines.total > 0
              ? (fileData.lines.covered / fileData.lines.total) * 100
              : 100,
          })
        }
      }
    }

    return {
      total: {
        lines: total.lines?.total || 0,
        covered: total.lines?.covered || 0,
        percentage: total.lines?.total
          ? (total.lines.covered / total.lines.total) * 100
          : 0,
      },
      files,
    }
  }

  return {
    total: { lines: 0, covered: 0, percentage: 0 },
    files: [],
  }
}
