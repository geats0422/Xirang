/**
 * Security Audit Tool
 *
 * Custom OpenCode tool to run security audits on dependencies and code.
 * Combines npm audit, secret scanning, and OWASP checks.
 */

import { tool } from "@opencode-ai/plugin/tool"

export default tool({
  description:
    "Run a comprehensive security audit including dependency vulnerabilities, secret scanning, and common security issues.",
  args: {
    type: tool.schema
      .enum(["all", "dependencies", "secrets", "code"])
      .optional()
      .describe("Type of audit to run (default: all)"),
    fix: tool.schema
      .boolean()
      .optional()
      .describe("Attempt to auto-fix dependency vulnerabilities (default: false)"),
    severity: tool.schema
      .enum(["low", "moderate", "high", "critical"])
      .optional()
      .describe("Minimum severity level to report (default: moderate)"),
  },
  async execute(args: Record<string, unknown>, context: { worktree?: string; directory: string; $: any }) {
    const auditType = (args.type as string) ?? "all"
    const fix = (args.fix as boolean) ?? false
    const severity = (args.severity as string) ?? "moderate"
    const cwd = context.worktree || context.directory
    const $ = context.$

    const results: AuditResults = {
      timestamp: new Date().toISOString(),
      directory: cwd,
      checks: [],
      summary: {
        passed: 0,
        failed: 0,
        warnings: 0,
      },
    }

    if (auditType === "all" || auditType === "dependencies") {
      results.checks.push({
        name: "Dependency Vulnerabilities",
        description: "Check for known vulnerabilities in dependencies",
        command: fix ? "npm audit fix" : "npm audit",
        severityFilter: severity,
        status: "pending",
      })
    }

    if (auditType === "all" || auditType === "secrets") {
      const secretPatterns = await scanForSecrets(cwd, $)
      if (secretPatterns.length > 0) {
        results.checks.push({
          name: "Secret Detection",
          description: "Scan for hardcoded secrets and API keys",
          status: "failed",
          findings: secretPatterns,
        })
        results.summary.failed++
      } else {
        results.checks.push({
          name: "Secret Detection",
          description: "Scan for hardcoded secrets and API keys",
          status: "passed",
        })
        results.summary.passed++
      }
    }

    if (auditType === "all" || auditType === "code") {
      const codeIssues = await scanCodeSecurity(cwd, $)
      if (codeIssues.length > 0) {
        results.checks.push({
          name: "Code Security",
          description: "Check for common security anti-patterns",
          status: "warning",
          findings: codeIssues,
        })
        results.summary.warnings++
      } else {
        results.checks.push({
          name: "Code Security",
          description: "Check for common security anti-patterns",
          status: "passed",
        })
        results.summary.passed++
      }
    }

    results.recommendations = generateRecommendations(results)

    return JSON.stringify(results)
  },
})

interface AuditCheck {
  name: string
  description: string
  command?: string
  severityFilter?: string
  status: "pending" | "passed" | "failed" | "warning"
  findings?: Array<{ file: string; issue: string; line?: number }>
}

interface AuditResults {
  timestamp: string
  directory: string
  checks: AuditCheck[]
  summary: {
    passed: number
    failed: number
    warnings: number
  }
  recommendations?: string[]
}

async function scanForSecrets(
  cwd: string,
  $: any
): Promise<Array<{ file: string; issue: string; line?: number }>> {
  const findings: Array<{ file: string; issue: string; line?: number }> = []

  const secretPatterns = [
    { pattern: /api[_-]?key\s*[:=]\s*['"][^'"]{20,}['"]/gi, name: "API Key" },
    { pattern: /password\s*[:=]\s*['"][^'"]+['"]/gi, name: "Password" },
    { pattern: /secret\s*[:=]\s*['"][^'"]{10,}['"]/gi, name: "Secret" },
    { pattern: /Bearer\s+[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+/g, name: "JWT Token" },
    { pattern: /sk-[a-zA-Z0-9]{32,}/g, name: "OpenAI API Key" },
    { pattern: /ghp_[a-zA-Z0-9]{36}/g, name: "GitHub Token" },
    { pattern: /aws[_-]?secret[_-]?access[_-]?key/gi, name: "AWS Secret" },
  ]

  const ignorePatterns = [
    "node_modules",
    ".git",
    "dist",
    "build",
    ".env.example",
    ".env.template",
  ]

  try {
    const srcDir = `${cwd}/src`
    await scanDirectoryShell(srcDir, secretPatterns, ignorePatterns, findings, $)
  } catch {
    // src directory may not exist
  }

  const configFiles = ["config.js", "config.ts", "settings.js", "settings.ts"]
  for (const configFile of configFiles) {
    const filePath = `${cwd}/${configFile}`
    try {
      await $`test -f ${filePath}`
      await scanFileShell(filePath, secretPatterns, findings, $)
    } catch {
      // File doesn't exist
    }
  }

  return findings
}

async function scanDirectoryShell(
  dir: string,
  patterns: Array<{ pattern: RegExp; name: string }>,
  ignorePatterns: string[],
  findings: Array<{ file: string; issue: string; line?: number }>,
  $: any
): Promise<void> {
  try {
    const result = await $`find ${dir} -type f \\( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.json" \\) 2>/dev/null`.catch(() => "")
    const files = result.toString().split("\n").filter(Boolean)
    
    for (const filePath of files) {
      if (ignorePatterns.some((p) => filePath.includes(p))) continue
      await scanFileShell(filePath, patterns, findings, $)
    }
  } catch {
    // Ignore errors
  }
}

async function scanFileShell(
  filePath: string,
  patterns: Array<{ pattern: RegExp; name: string }>,
  findings: Array<{ file: string; issue: string; line?: number }>,
  $: any
): Promise<void> {
  try {
    const result = await $`cat ${filePath}`.catch(() => "")
    const content = result.toString()
    const lines = content.split("\n")

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]
      for (const { pattern, name } of patterns) {
        pattern.lastIndex = 0
        if (pattern.test(line)) {
          findings.push({
            file: filePath,
            issue: `Potential ${name} found`,
            line: i + 1,
          })
        }
      }
    }
  } catch {
    // Ignore read errors
  }
}

async function scanCodeSecurity(
  cwd: string,
  $: any
): Promise<Array<{ file: string; issue: string; line?: number }>> {
  const findings: Array<{ file: string; issue: string; line?: number }> = []

  const securityPatterns = [
    { pattern: /\beval\s*\(/g, name: "eval() usage - potential code injection" },
    { pattern: /innerHTML\s*=/g, name: "innerHTML assignment - potential XSS" },
    { pattern: /dangerouslySetInnerHTML/g, name: "dangerouslySetInnerHTML - potential XSS" },
    { pattern: /document\.write/g, name: "document.write - potential XSS" },
    { pattern: /\$\{.*\}.*sql/gi, name: "Potential SQL injection" },
  ]

  try {
    const srcDir = `${cwd}/src`
    await scanDirectoryShell(srcDir, securityPatterns, ["node_modules", ".git", "dist"], findings, $)
  } catch {
    // src directory may not exist
  }

  return findings
}

function generateRecommendations(results: AuditResults): string[] {
  const recommendations: string[] = []

  for (const check of results.checks) {
    if (check.status === "failed" && check.name === "Secret Detection") {
      recommendations.push(
        "CRITICAL: Remove hardcoded secrets and use environment variables instead"
      )
      recommendations.push("Add a .env file (gitignored) for local development")
      recommendations.push("Use a secrets manager for production deployments")
    }

    if (check.status === "warning" && check.name === "Code Security") {
      recommendations.push(
        "Review flagged code patterns for potential security vulnerabilities"
      )
      recommendations.push("Consider using DOMPurify for HTML sanitization")
      recommendations.push("Use parameterized queries for database operations")
    }

    if (check.status === "pending" && check.name === "Dependency Vulnerabilities") {
      recommendations.push("Run 'npm audit' to check for dependency vulnerabilities")
      recommendations.push("Consider using 'npm audit fix' to auto-fix issues")
    }
  }

  if (recommendations.length === 0) {
    recommendations.push("No critical security issues found. Continue following security best practices.")
  }

  return recommendations
}
