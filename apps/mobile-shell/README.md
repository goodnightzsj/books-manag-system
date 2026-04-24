# Mobile Shell (Capacitor)

Wraps `frontend/reader-web` as an Android / iOS app.

## Dev flow

```bash
npm install
# option A: live-reload against local reader-web
# -> open http://10.0.2.2:3001 from the emulator; edit capacitor.config.json
# option B: static bundle
cd ../../frontend/reader-web && npm run build
cd - && npm run cap:init && npm run cap:add:android && npm run cap:sync
npm run cap:open:android
```

The shell only ships the WebView + native permissions; all business
logic lives in the reader web app.
