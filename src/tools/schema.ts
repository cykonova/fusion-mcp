import { z } from "zod";

/**
 * MCP transport may send boolean values as strings ("true"/"false").
 * z.coerce.boolean() is unsafe because any truthy string (including "false") becomes true.
 * This preprocessor handles string-to-boolean conversion correctly.
 */
export const zBool = () =>
  z.preprocess(v => v === "true" ? true : v === "false" ? false : v, z.boolean());
