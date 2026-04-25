// Copy the prebuilt pdfjs worker into /public so PdfReader can reference
// it as a same-origin static asset. Avoids webpack parsing the ESM worker
// (which fails because the file uses top-level import/export and webpack
// tries to re-bundle it).

import { copyFileSync, existsSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);

const pkgPath = require.resolve("pdfjs-dist/package.json");
const root = dirname(pkgPath);

const candidates = [
  "build/pdf.worker.min.mjs",
  "build/pdf.worker.mjs",
  "legacy/build/pdf.worker.min.mjs",
];
const src = candidates
  .map((rel) => resolve(root, rel))
  .find((p) => existsSync(p));

if (!src) {
  console.error("pdf.worker not found in pdfjs-dist; checked:", candidates);
  process.exit(1);
}

const publicDir = resolve(here, "..", "public");
mkdirSync(publicDir, { recursive: true });
const dest = resolve(publicDir, "pdf.worker.min.mjs");
copyFileSync(src, dest);
console.log(`copied ${src} -> ${dest}`);
