import type { Plugin } from "@opencode-ai/plugin";

const ALLOWED_DOC_PATTERNS = [
  /README/i,
  /CLAUDE/i,
  /CONTRIBUTING/i,
  /CHANGELOG/i,
  /LICENSE/i,
  /SKILL/i,
  /AGENTS/i,
  /\/docs\//i,
  /\/skills\//i,
  /\/examples\//i,
];

const DOC_EXTENSIONS = [".md", ".txt", ".rst", ".adoc"];

export const DocFileWarning: Plugin = async ({ client }) => {
  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool === "write") {
        const filePath = output.args.file_path || "";
        
        const isDocFile = DOC_EXTENSIONS.some((ext) => 
          filePath.toLowerCase().endsWith(ext)
        );
        
        if (isDocFile) {
          const isAllowed = ALLOWED_DOC_PATTERNS.some((pattern) => 
            pattern.test(filePath)
          );
          
          if (!isAllowed) {
            console.error(
              "[Hook] Warning: Creating non-standard documentation file\n" +
                `[Hook] File: ${filePath}\n` +
                "[Hook] Consider using standard locations: docs/, skills/, examples/\n" +
                "[Hook] Allowed: README, CLAUDE, CONTRIBUTING, CHANGELOG, LICENSE, SKILL, AGENTS"
            );
          }
        }
      }
    },
  };
};
