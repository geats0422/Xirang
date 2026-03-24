import type { Plugin } from "@opencode-ai/plugin";

export const WorkflowInjectorPlugin: Plugin = async () => {
  return {
    event: async ({ event }) => {
      if (event.type === "session.created") {
        console.log("[Workflow] Design-first workflow rules loaded");
        console.log("[Workflow] Use /brainstorm -> /plan -> /execute -> /finish");
      }
    }
  };
};
