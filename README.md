# ResQ-Flow Integration

ResQ-Flow combines a FastAPI service with a Flutter client for authenticated
SOS reporting and rescue coordination. The mobile client persists SOS reports
locally before attempting an idempotent sync. Supabase stores application data
and authenticates users; the backend validates Supabase access tokens and
enforces victim, rescuer, and administrator permissions.

## Backend

1. In the Supabase SQL editor, apply
   `backend/migrations/000_initial_schema.sql` followed by
   `backend/migrations/001_integration_safety.sql`. The initial migration uses
   `CREATE TABLE IF NOT EXISTS` and enables RLS; only the server's service-role
   key can access application tables. Existing tables are not rebuilt.
2. Create a `profiles` row with the same ID as each Supabase Auth user and a
   `VICTIM`, `RESCUER`, or `ADMIN` role. The API rejects users without a valid
   profile.
3. In `backend`, copy `.env.example` to `.env` and provide the Supabase URL,
   publishable key, and server-only secret/service-role key.
4. `001_integration_safety.sql` is additive and safe to rerun. If existing
   duplicate `(user_id, local_id)` values are found, resolve them before
   retrying; the migration does not delete incident data.
5. Install and start the API:

   ```powershell
   cd backend
   python -m pip install -r requirements.txt
   python -m uvicorn main:app --reload
   ```

   API documentation is available at `http://127.0.0.1:8000/docs`.

   For backend tests, install `requirements-dev.txt` and run
   `python -m pytest -q tests` from `backend`.

The backend's `/api/incidents/{id}/analyze` endpoint uses transparent,
deterministic triage rules and reports that no ML model was used. Priority
scores include their contributing factors. Resource recommendations reflect
recorded availability only and do not reserve or dispatch resources.

## Flutter client

See [`mobile/README.md`](mobile/README.md) for the Supabase/FastAPI build
configuration and run instructions. Never place a Supabase secret or
service-role key in the mobile app.

## Checks

```powershell
cd backend
python -m pytest -q tests
cd ..\mobile
flutter analyze
flutter test
```
