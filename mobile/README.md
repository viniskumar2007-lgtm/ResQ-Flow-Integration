# ResQ-Flow mobile client

The Flutter app uses Supabase Auth for sign-in and sends the active Supabase
access token to the FastAPI backend. SOS reports are written to a local SQLite
outbox before a network sync is attempted. Each report receives a stable
`local_id`; failed requests stay queued and are retried at app launch or when
the user taps refresh. Local outbox records are scoped to the signed-in user.

The app requests GPS only when the user chooses to attach their location.
Incident coordinates are displayed on an OpenStreetMap map. Resource
availability is shown as reported inventory, not as a confirmed dispatch.
Priority analysis is explicitly rule-based; no machine-learning model is
claimed or configured. The app does not implement Bluetooth, Wi-Fi Direct, or
mesh forwarding.

## Run

From the repository root, pass configuration at build time; do not add keys to
the Dart source or commit a `--dart-define` file:

```powershell
cd mobile
flutter pub get
flutter run `
  --dart-define=SUPABASE_URL=https://your-project.supabase.co `
  --dart-define=SUPABASE_PUBLISHABLE_KEY=your-publishable-key `
  --dart-define=RESQ_API_BASE_URL=http://10.0.2.2:8000
```

Use `http://10.0.2.2:8000` only for a local Android emulator; the debug Android
manifest permits cleartext traffic for development builds only. Configure an
HTTPS API URL for deployed/release builds. On iOS, use a reachable development
host instead of the Android emulator address.
