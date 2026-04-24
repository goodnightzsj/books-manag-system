# Desktop Shell (Tauri 2)

Wraps `frontend/reader-web` as Windows / macOS / Linux desktop app.

## Dev

```bash
npm install
npm run dev
```

`tauri.conf.json` points `beforeDevCommand` to the reader-web dev
server (port 3001). `npm run build` produces platform-native bundles
under `src-tauri/target/release/bundle/`.
