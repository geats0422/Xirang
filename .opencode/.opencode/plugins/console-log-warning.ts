import type { Plugin } from "@opencode-ai/plugin";

const CODE_EXTENSIONS = [
  ".ts", ".tsx", ".js", ".jsx", ".py", ".java", ".go", ".rs", 
  ".c", ".cpp", ".h", ".hpp", ".cs", ".rb", ".php", ".swift", ".kt"
];

const CONSOLE_PATTERNS = [
  /console\.log\(/,
  /console\.debug\(/,
  /console\.info\(/,
  /console\.warn\(/,
  /print\(/,
  /fmt\.Print/,
  /fmt\.Printf/,
  /log\./,
  /logger\./,
  /System\.out\.print/,
  /NSLog\(/,
  /println\(/,
  /logger\.Info/,
  /logger\.Debug/,
  /logger\.Warn/,
  /logger\.Error/,
  /logging\.info/,
  /logging\.debug/,
  /logging\.warning/,
  /logging\.error/,
];

export const ConsoleLogWarning: Plugin = async ({ client }) => {
  return {
    "tool.execute.after": async (input, output) => {
      if (input.tool === "edit" || input.tool === "write") {
        const filePath = (output as any).args?.file_path || "";
        
        const isCodeFile = CODE_EXTENSIONS.some((ext) => 
          filePath.toLowerCase().endsWith(ext)
        );
        
        if (isCodeFile) {
          const content = (output as any).args?.content || "";
          const matches = CONSOLE_PATTERNS.filter((pattern) => pattern.test(content));
          
          if (matches.length > 0) {
            console.error(
              `[Plugin] Warning: Found ${matches.length} logging statement(s) in ${filePath}\n` +
                "[Plugin] Consider removing debug logs before committing\n" +
                "[Plugin] Use appropriate logging levels (debug, info, warn, error)"
            );
          }
        }
      }
    },
  };
};
