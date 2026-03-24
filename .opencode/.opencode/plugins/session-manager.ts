import type { Plugin } from "@opencode-ai/plugin";

const SESSION_DIR = ".opencode/sessions";
const SESSION_FILE = `${SESSION_DIR}/last-session.json`;

interface SessionState {
  lastSessionTime?: number;
  toolCallCount?: number;
  projectContext?: string;
  activeFiles?: string[];
}

export const SessionManager: Plugin = async ({ directory }) => {
  return {
    event: async ({ event }) => {
      if (event.type === "session.created") {
        console.log("[Session] Session created");
      } else if (event.type === "session.compacted") {
        console.log("[Session] Context compacted - key information preserved");
      } else if (event.type === "session.deleted") {
        console.log("[Session] Session deleted");
      } else if (event.type === "session.idle") {
        console.log("[Session] Session idle");
      } else if (event.type === "session.updated") {
      }
    },
  };
};
