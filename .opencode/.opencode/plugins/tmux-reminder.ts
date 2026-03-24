import type { Plugin } from "@opencode-ai/plugin";

export const TmuxReminder: Plugin = async () => {
  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool === "bash") {
        const command = (input as any).args?.command || "";
        const longRunningPatterns = [
          /npm\s+(install|test|run\s+build)\b/,
          /pnpm\s+(install|test|build)\b/,
          /yarn\s+(install|test|build)\b/,
          /bun\s+(install|test|build)\b/,
          /pip\s+install\b/,
          /python\s+-m\s+pytest\b/,
          /python\s+-m\s+ unittest\b/,
          /cargo\s+build\b/,
          /cargo\s+test\b/,
          /docker\s+build\b/,
          /docker\s+run\b/,
          /make\b/,
          /gradle\b/,
          /dotnet\s+build\b/,
          /dotnet\s+test\b/,
        ];

        const isLongRunning = longRunningPatterns.some((pattern) => pattern.test(command));

        if (isLongRunning) {
          console.error(
            "[Hook] Consider running this in a persistent terminal for session persistence\n" +
              "[Hook] Recommended: VS Code terminal or Windows Terminal"
          );
        }
      }
    },
  };
};
