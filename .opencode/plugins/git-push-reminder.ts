import type { Plugin } from "@opencode-ai/plugin";

export const GitPushReminder: Plugin = async ({ client }) => {
  return {
    "tool.execute.before": async (input, output) => {
      if (input.tool === "bash") {
        const command = output.args.command || "";
        
        if (/git\s+push/.test(command)) {
          console.error(
            "[Hook] Reminder: Review changes before pushing to remote\n" +
              "[Hook] Consider running: git diff HEAD~1..HEAD\n" +
              "[Hook] Or: git log --oneline -n 5"
          );
        }
      }
    },
  };
};
