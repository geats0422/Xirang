import type { Plugin } from "@opencode-ai/plugin";

const JS_TS_EXTENSIONS = [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"];

export const AutoFormat: Plugin = async ({ client, $ }) => {
  return {
    "tool.execute.after": async (input, output) => {
      if (input.tool === "edit" || input.tool === "write") {
        const filePath = (input as any).args?.file_path || "";
        
        const isJsTsFile = JS_TS_EXTENSIONS.some((ext) => 
          filePath.toLowerCase().endsWith(ext)
        );
        
        if (isJsTsFile) {
          try {
            const biomeExists = await $`which biome`.catch(() => false);
            if (biomeExists) {
              await $`biome format --write ${filePath}`;
              return;
            }
            
            const prettierExists = await $`which prettier`.catch(() => false);
            if (prettierExists) {
              await $`prettier --write ${filePath}`;
              return;
            }
            
            const eslintFixExists = await $`which eslint`.catch(() => false);
            if (eslintFixExists) {
              await $`eslint --fix ${filePath}`;
            }
          } catch (error) {
            console.error("[Hook] Auto-format failed:", error);
          }
        }
      }
    },
  };
};
