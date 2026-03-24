import type { Plugin } from "@opencode-ai/plugin";

export const DevServerBlocker: Plugin = async () => {
  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool === "bash") {
        const command = (input as any).args?.command || "";
        const devPatterns = [
          /npm\s+run\s+dev\b/,
          /pnpm\s+(run\s+)?dev\b/,
          /yarn\s+dev\b/,
          /bun\s+(run\s+)?dev\b/,
          /python\s+-m\s+uvicorn\b/,
          /python\s+manage\.py\s+runserver\b/,
          /flask\s+run\b/,
          /django-admin\s+runserver\b/,
          /node\s+.+server\.js\b/,
        ];

        const isDevServer = devPatterns.some((pattern) => pattern.test(command));

        if (isDevServer) {
          throw new Error(
            "[Hook] BLOCKED: Dev server should run in a persistent terminal for log access\n" +
              "[Hook] Recommended: Run in a separate terminal or use VS Code terminal\n" +
              "[Hook] On Windows: Use Windows Terminal or keep the terminal open"
          );
        }
      }
    },
  };
};
