# src/ — TypeScript MCP Server

See root [CLAUDE.md](../CLAUDE.md) for project overview.

## Adding a New Tool Module

1. Create `src/tools/<category>.ts`
2. Export `registerXxxTools(server: McpServer, bridge: FusionBridge): void`
3. Import and call it in `src/tools/index.ts`

## Tool Registration Pattern

```ts
server.registerTool("fusion_<action>", {
  description: "...",
  inputSchema: {
    param: z.string().describe("..."),
    num: z.coerce.number().describe("..."),    // always coerce numbers
    flag: zBool().default(false).describe("..."), // always use zBool() for booleans
  },
}, async (args) => {
  const result = await bridge.call("category.action", args);
  return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
});
```

## Key Files

- `tools/index.ts` — Registration hub, imports all tool modules
- `tools/schema.ts` — `zBool()` helper for safe boolean coercion
- `bridge/fusion-bridge.ts` — HTTP client to Fusion add-in
