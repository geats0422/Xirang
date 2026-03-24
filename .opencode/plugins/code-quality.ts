import type { Plugin } from "@opencode-ai/plugin";

export const CodeQualityPlugin: Plugin = async ({ client }) => {
  return {
    "file.edited": async (input: { filePath: string }) => {
      const filePath = input.filePath;
      const ext = filePath.split(".").pop()?.toLowerCase();

      const frontendExts = ["ts", "tsx", "js", "jsx", "vue", "svelte"];
      const backendExts = ["py", "go", "rs", "java", "ts", "js"];
      const dbExts = ["sql", "pgsql"];

      if (frontendExts.includes(ext || "")) {
        console.log("[CodeQuality] Frontend file edited:", filePath);
        console.log("[CodeQuality] Run /quality for quality assessment");
      } else if (backendExts.includes(ext || "")) {
        console.log("[CodeQuality] Backend file edited:", filePath);
        console.log("[CodeQuality] Run /quality for quality assessment");
      } else if (dbExts.includes(ext || "")) {
        console.log("[CodeQuality] Database file edited:", filePath);
        console.log("[CodeQuality] Run /quality for quality assessment");
      }
    },
    "tool.execute.after": async (input: { tool: string; args: any }) => {
      if (input.tool === "bash") {
        const command = input.args?.command || "";
        
        if (/git\s+(commit|push)/.test(command)) {
          console.log("[CodeQuality] Consider running /quality before committing");
        }
      }
    }
  };
};
