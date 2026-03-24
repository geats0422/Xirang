import type { Plugin } from "@opencode-ai/plugin";

let toolCallCount = 0;
const COMPACT_INTERVAL = 50;

export const StrategicCompact: Plugin = async ({ client }) => {
  return {
    "tool.execute.after": async (input, output) => {
      toolCallCount++;
      
      if (toolCallCount >= COMPACT_INTERVAL) {
        console.error(
          `[Hook] Context management reminder (${toolCallCount} tool calls)\n` +
            "[Hook] Consider using /compact command to preserve context\n" +
            "[Hook] Best practice: Compact at logical breakpoints (feature complete, milestone reached)"
        );
        toolCallCount = 0;
      }
    },
  };
};
