import type { Plugin } from "@opencode-ai/plugin";

const TS_EXTENSIONS = [".ts", ".tsx"];

export const TypeScriptCheck: Plugin = async ({ client, $ }) => {
  return {
    "tool.execute.after": async (input, output) => {
      if (input.tool === "edit" || input.tool === "write") {
        const filePath = (output as any).args?.file_path || "";
        
        const isTsFile = TS_EXTENSIONS.some((ext) => 
          filePath.toLowerCase().endsWith(ext)
        );
        
        if (isTsFile) {
          try {
            const tscExists = await $`which tsc`.catch(() => false);
            if (tscExists) {
              const result = await $`tsc --noEmit ${filePath} 2>&1`.catch(() => "") as string;
              if (result && result.toString().trim()) {
                console.error("[Plugin] TypeScript errors detected:");
                console.error(result);
              }
            }
          } catch (error) {
            console.error("[Plugin] TypeScript check failed:", error);
          }
        }
      }
    },
  };
};
