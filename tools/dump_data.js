#!/usr/bin/env node
// Load one or more course data files (data.js, meta.js) in a sandbox and print
// everything they put on `window` as JSON. Used by tools/check.py and tools/evolve.py.
// Usage: node tools/dump_data.js meta.js data.js
"use strict";
const fs = require("fs");
const vm = require("vm");

// In a browser `window` is the global object, so data files may also use bare names
// (e.g. TRUNK.breaks). Make the sandbox global behave the same way.
const ctx = vm.createContext({});
vm.runInContext("var window = globalThis;", ctx);
for (const f of process.argv.slice(2)) {
  vm.runInContext(fs.readFileSync(f, "utf8"), ctx, { filename: f, timeout: 5000 });
}
const out = {};
for (const k of Object.keys(ctx)) if (k !== "window") out[k] = ctx[k];
process.stdout.write(JSON.stringify(out));
