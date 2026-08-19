# Repository instructions

## Verification

Use the Makefile targets. Before handing off add-on changes, run:

```sh
make lint typecheck test check-package
make qt-smoke
```

`make check-package` rebuilds `dist/lofi-town.ankiaddon` before validating it.

## Local focus-sync end-to-end testing

The add-on must use a disposable Anki profile and the Lofi Town stack must use
disposable local PostgreSQL and Redis instances. Never run this test with a
remote database or Redis URL.

### 1. Start disposable data services

Use unique container names and loopback-only ports:

```sh
docker run --name lofi-anki-e2e-postgres --rm -d \
  -e POSTGRES_PASSWORD=lofi_anki_e2e \
  -e POSTGRES_DB=lofi_town \
  -p 127.0.0.1:55439:5432 postgres:16

docker run --name lofi-anki-e2e-redis --rm -d \
  -p 127.0.0.1:56389:6379 redis:7
```

In the paired Lofi Town checkout, apply migrations to that database:

```sh
POSTGRES_PRISMA_URL='postgresql://postgres:lofi_anki_e2e@127.0.0.1:55439/lofi_town?schema=public' \
POSTGRES_URL_NON_POOLING='postgresql://postgres:lofi_anki_e2e@127.0.0.1:55439/lofi_town?schema=public' \
  npm run migrate:deploy --workspace=@realms/db
```

### 2. Start the guarded Lofi Town stack

Use `npm run dev:anki-e2e`, not `npm run dev:web`. The guarded command rejects
non-loopback data service URLs, forces the local service endpoints, and passes
the overrides through Turborepo. Authentication settings still come from the
checkout's ignored `.env` files.

```sh
POSTGRES_PRISMA_URL='postgresql://postgres:lofi_anki_e2e@127.0.0.1:55439/lofi_town?schema=public' \
POSTGRES_URL_NON_POOLING='postgresql://postgres:lofi_anki_e2e@127.0.0.1:55439/lofi_town?schema=public' \
REDIS_URL='redis://127.0.0.1:56389' \
  npm run dev:anki-e2e
```

Before signing in, verify ports 3000, 4200, 4300, and 4400 are listening and
that the service processes connect only to `127.0.0.1:55439` and
`127.0.0.1:56389` for application data. Do not continue if a data connection
uses a remote host.

### 3. Launch isolated Anki

Build the package and install it into a temporary base folder. Do not use the
normal Anki profile or the source add-on's persistent browser profile.

```sh
make check-package
ANKI_E2E_BASE=$(mktemp -d /tmp/lofi-anki-e2e.XXXXXX)
mkdir -p "$ANKI_E2E_BASE/addons21/lofi_town"
unzip -q dist/lofi-town.ankiaddon -d "$ANKI_E2E_BASE/addons21/lofi_town"

ANKI_SINGLE_INSTANCE_KEY=lofi-anki-e2e \
LOFI_TOWN_ANKI_DEV_URL=http://localhost:3000 \
  /Applications/Anki.app/Contents/MacOS/Anki \
  -b "$ANKI_E2E_BASE" -p 'User 1' -l en
```

`LOFI_TOWN_ANKI_DEV_URL` accepts only plain HTTP loopback origins. Keep the
unique `ANKI_SINGLE_INSTANCE_KEY` so the disposable instance can run without
replacing the user's normal Anki process. When stopping it, target the exact
isolated PID. Do not use a generic Quit action that could close normal Anki.

### 4. Exercise the contract

Use disposable cards and enable "Sync focus time and rewards with Lofi Town."
Verify:

- The HUD says Ready before the first answer.
- The first answer creates one private solo stopwatch.
- Additional answers reuse the same session.
- Pause and resume synchronize in both clients.
- Reloading the panel reconciles the owned session.
- Leaving the reviewer ends only the Anki-owned session.
- The local `FocusSession` table records one stopwatch session.

If OAuth shows an account chooser or requests new consent, stop and let the
user choose the account. Never guess among signed-in accounts.

### 5. Clean up

Stop the isolated Anki PID and Lofi Town process, then remove the disposable
containers:

```sh
docker stop lofi-anki-e2e-postgres lofi-anki-e2e-redis
```

The containers use `--rm`, so stopping them deletes the test database and Redis
data. Move the temporary Anki base folder to Trash when practical. Confirm the
six local ports are no longer listening. If normal Anki was running before the
test, make sure it is still running afterward.
