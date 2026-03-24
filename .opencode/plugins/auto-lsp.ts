/**
 * Auto-LSP Plugin - 自动检测项目语言并配置 LSP
 * 
 * 支持的 LSP 服务器列表: https://opencode.ai/docs/zh-cn/lsp/
 */

import type { PluginInput } from "@opencode-ai/plugin"

const LANGUAGE_LSP_MAP: Record<string, { name: string; install: string; config: string; extensions: string[] }> = {
  typescript: {
    name: "typescript-language-server",
    install: "npm install -g typescript-language-server typescript",
    config: "typescript",
    extensions: [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts"]
  },
  python: {
    name: "pyright",
    install: "pip install pyright 或 npm install -g pyright",
    config: "pyright",
    extensions: [".py", ".pyi"]
  },
  go: {
    name: "gopls",
    install: "go install golang.org/x/tools/gopls@latest",
    config: "gopls",
    extensions: [".go"]
  },
  rust: {
    name: "rust-analyzer",
    install: "rustup component add rust-analyzer",
    config: "rust-analyzer",
    extensions: [".rs"]
  },
  java: {
    name: "jdtls",
    install: "需要安装 Java SDK (version 21+)",
    config: "jdtls",
    extensions: [".java"]
  },
  cpp: {
    name: "clangd",
    install: "安装 clangd (LLVM 的一部分)",
    config: "clangd",
    extensions: [".c", ".cpp", ".cc", ".cxx", ".c++", ".h", ".hpp", ".hh", ".hxx", ".h++"]
  },
  csharp: {
    name: "omnisharp",
    install: "dotnet tool install --global omnisharp",
    config: "omnisharp",
    extensions: [".cs"]
  },
  deno: {
    name: "deno",
    install: "deno (自动检测 deno.json/deno.jsonc)",
    config: "deno",
    extensions: [".ts", ".tsx", ".js", ".jsx", ".mjs"]
  },
  eslint: {
    name: "eslint",
    install: "项目中需要 eslint 依赖",
    config: "eslint",
    extensions: [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts", ".vue"]
  },
  oxlint: {
    name: "oxlint",
    install: "项目中需要 oxlint 依赖",
    config: "oxlint",
    extensions: [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts", ".vue", ".astro", ".svelte"]
  },
  astro: {
    name: "astro-language-server",
    install: "为 Astro 项目自动安装",
    config: "astro",
    extensions: [".astro"]
  },
  bash: {
    name: "bash-language-server",
    install: "npm install -g bash-language-server",
    config: "bash",
    extensions: [".sh", ".bash", ".zsh", ".ksh"]
  },
  clojure: {
    name: "clojure-lsp",
    install: "需要 clojure-lsp 命令可用",
    config: "clojure-lsp",
    extensions: [".clj", ".cljs", ".cljc", ".edn"]
  },
  dart: {
    name: "dart-language-server",
    install: "需要 dart 命令可用",
    config: "dart",
    extensions: [".dart"]
  },
  elixir: {
    name: "elixir-ls",
    install: "需要 elixir 命令可用",
    config: "elixir-ls",
    extensions: [".ex", ".exs"]
  },
  fsharp: {
    name: "fsharp-language-server",
    install: "需要已安装 .NET SDK",
    config: "fsharp",
    extensions: [".fs", ".fsi", ".fsx", ".fsscript"]
  },
  gleam: {
    name: "gleam-language-server",
    install: "需要 gleam 命令可用",
    config: "gleam",
    extensions: [".gleam"]
  },
  haskell: {
    name: "haskell-language-server",
    install: "需要 haskell-language-server-wrapper 命令可用",
    config: "hls",
    extensions: [".hs", ".lhs"]
  },
  julia: {
    name: "julialals",
    install: "需要安装 julia 和 LanguageServer.jl",
    config: "julials",
    extensions: [".jl"]
  },
  kotlin: {
    name: "kotlin-language-server",
    install: "为 Kotlin 项目自动安装",
    config: "kotlin-ls",
    extensions: [".kt", ".kts"]
  },
  lua: {
    name: "lua-language-server",
    install: "为 Lua 项目自动安装",
    config: "lua-ls",
    extensions: [".lua"]
  },
  nix: {
    name: "nixd",
    install: "需要 nixd 命令可用",
    config: "nixd",
    extensions: [".nix"]
  },
  ocaml: {
    name: "ocaml-lsp",
    install: "需要 ocamllsp 命令可用",
    config: "ocaml-lsp",
    extensions: [".ml", ".mli"]
  },
  php: {
    name: "intelephense",
    install: "为 PHP 项目自动安装 (高级功能需要许可证)",
    config: "php",
    extensions: [".php"]
  },
  prisma: {
    name: "prisma-language-server",
    install: "需要 prisma 命令可用",
    config: "prisma",
    extensions: [".prisma"]
  },
  ruby: {
    name: "ruby-lsp",
    install: "需要 ruby 和 gem 命令可用",
    config: "ruby-lsp",
    extensions: [".rb", ".rake", ".gemspec", ".ru"]
  },
  swift: {
    name: "sourcekit-lsp",
    install: "需要已安装 swift (macOS 上为 xcode)",
    config: "sourcekit-lsp",
    extensions: [".swift", ".objc", ".objcpp"]
  },
  svelte: {
    name: "svelte-language-server",
    install: "为 Svelte 项目自动安装",
    config: "svelte",
    extensions: [".svelte"]
  },
  terraform: {
    name: "terraform-ls",
    install: "从 GitHub releases 自动安装",
    config: "terraform",
    extensions: [".tf", ".tfvars"]
  },
  tinymist: {
    name: "tinymist",
    install: "从 GitHub releases 自动安装",
    config: "tinymist",
    extensions: [".typ", ".typc"]
  },
  vue: {
    name: "vue-language-server",
    install: "为 Vue 项目自动安装",
    config: "vue",
    extensions: [".vue"]
  },
  yaml: {
    name: "yaml-language-server",
    install: "自动安装 Red Hat yaml-language-server",
    config: "yaml-ls",
    extensions: [".yaml", ".yml"]
  },
  zig: {
    name: "zls",
    install: "需要 zig 命令可用",
    config: "zls",
    extensions: [".zig", ".zon"]
  }
}

const EXTENSION_LANG_MAP: Record<string, string> = {}

for (const [lang, lsp] of Object.entries(LANGUAGE_LSP_MAP)) {
  for (const ext of lsp.extensions) {
    EXTENSION_LANG_MAP[ext] = lang
  }
}

function getLanguageFromExtension(filename: string): string | null {
  const ext = filename.substring(filename.lastIndexOf("."))
  return EXTENSION_LANG_MAP[ext] || null
}

export const AutoLSPPlugin = async ({
  client,
  $,
  directory,
  worktree,
}: PluginInput) => {
  const log = (level: "info" | "warn", message: string) => {
    client.app.log({ body: { service: "auto-lsp", level, message } })
  }

  const runLs = async (dirPath: string): Promise<string[]> => {
    try {
      const result = await $`ls ${dirPath}`
      const text = await result.text()
      return text.split("\n").filter((line: string) => line.trim())
    } catch {
      return []
    }
  }

  const scanFiles = async (dirPath: string): Promise<string[]> => {
    try {
      const result = await $`find ${dirPath} -type f -name "*.*" 2>/dev/null | head -100`
      const text = await result.text()
      return text.split("\n").filter((line: string) => line.trim())
    } catch {
      return []
    }
  }

  return {
    "session.created": async () => {
      log("info", "[Auto-LSP] 检测项目语言...")

      try {
        const baseDir = worktree || directory
        const files = await scanFiles(baseDir)
        
        const languages = new Set<string>()
        const fileExtensions = new Set<string>()
        
        for (const filepath of files) {
          const filename = filepath.split("/").pop() || filepath.split("\\").pop() || ""
          const ext = filename.substring(filename.lastIndexOf("."))
          if (ext) {
            fileExtensions.add(ext)
            const lang = getLanguageFromExtension(filename)
            if (lang) {
              languages.add(lang)
            }
          }
        }

        if (languages.size === 0) {
          const lines = await runLs(baseDir)
          for (const filename of lines) {
            const lang = getLanguageFromExtension(filename)
            if (lang) {
              languages.add(lang)
            }
          }
        }

        if (languages.size === 0) {
          log("info", "[Auto-LSP] 未检测到项目语言")
          return
        }

        const langArray = Array.from(languages)
        log("info", `[Auto-LSP] 检测到: ${langArray.join(", ")}`)

        for (const lang of langArray) {
          const lsp = LANGUAGE_LSP_MAP[lang]
          if (lsp) {
            log("info", `[Auto-LSP] ${lang} → ${lsp.name}`)
          }
        }

        log("info", "[Auto-LSP] 运行 /setup-lsp 获取完整配置")
      } catch (err) {
        log("warn", `[Auto-LSP] 错误: ${err}`)
      }
    },

    tool: {
      setupLsp: {
        description: "检测项目语言并提供 LSP 安装建议",
        args: {},
        async execute() {
          try {
            const baseDir = worktree || directory
            const files = await scanFiles(baseDir)
            
            const languages = new Set<string>()
            const fileExtensions = new Set<string>()
            
            for (const filepath of files) {
              const filename = filepath.split("/").pop() || filepath.split("\\").pop() || ""
              const ext = filename.substring(filename.lastIndexOf("."))
              if (ext) {
                fileExtensions.add(ext)
                const lang = getLanguageFromExtension(filename)
                if (lang) {
                  languages.add(lang)
                }
              }
            }

            if (languages.size === 0) {
              const lines = await runLs(baseDir)
              for (const filename of lines) {
                const lang = getLanguageFromExtension(filename)
                if (lang) {
                  languages.add(lang)
                }
              }
            }

            if (languages.size === 0) {
              return "未检测到项目语言，请在项目中创建一些代码文件后再试。"
            }

            const langArray = Array.from(languages)
            let output = `# 检测到的语言: ${langArray.join(", ")}\n\n`
            output += `## 建议安装的 LSP:\n\n`

            for (const lang of langArray) {
              const lsp = LANGUAGE_LSP_MAP[lang]
              if (lsp) {
                output += `### ${lang}\n`
                output += `- LSP: **${lsp.name}**\n`
                output += `- 安装: \`${lsp.install}\`\n`
                output += `- 文件扩展名: ${lsp.extensions.join(", ")}\n\n`
              }
            }

            output += `## 在 opencode.json 中配置:\n`
            output += "```json\n{\n  \"lsp\": {\n"
            for (const lang of langArray) {
              const lsp = LANGUAGE_LSP_MAP[lang]
              if (lsp) {
                output += `    \"${lsp.config}\": { \"enabled\": true },\n`
              }
            }
            output += "  }\n}\n```\n"

            output += "\n## 注意事项\n"
            output += "- OpenCode 会自动检测上述文件扩展名并启用对应的 LSP 服务器\n"
            output += "- 确保已安装对应的语言运行时和 LSP 服务器\n"
            output += "- 某些 LSP 需要在项目中安装依赖 (如 eslint, oxlint)\n"

            return output
          } catch (err) {
            return `检测失败: ${err}`
          }
        }
      }
    }
  }
}

export default AutoLSPPlugin
