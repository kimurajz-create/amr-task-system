# AMR Task System Packaging Guide

## Recommended Packaging Mode

Use `PyInstaller` in `onedir` mode.

Reason:
- The executable and editable config files can stay in the same folder.
- On the target PC, you can change JSON files without rebuilding.
- This project uses map assets and site profiles, so `onedir` is easier to inspect and maintain than `onefile`.

The current [`main.spec`](./main.spec) already packages:
- `site/`
- `picture/`
- `app_settings.json`
- `config.json`
- `db_config.json`

## Config Files

These files are intended to stay next to the executable after packaging:

- `app_settings.json`
  Used for selecting the active site profile, for example `company` or `hospital`.

- `config.json`
  Used for MiR runtime settings such as `MIR_IP`.

- `db_config.json`
  Used for PostgreSQL connection settings.

## Runtime Behavior After This Update

When the app is packaged:

1. It now prefers config files located next to the executable.
2. If an external file is missing, it can still fall back to the bundled copy.
3. Saving `config.json` writes back to the executable folder instead of depending on the current working directory.

This is important when the app is launched by double-click, shortcut, or another shell.

## Build Command

From the project root:

```powershell
pyinstaller --noconfirm main.spec
```

Build output:

- Executable folder: `dist/main/`
- Executable: `dist/main/main.exe`

## Files To Bring To Another PC

Copy the whole `dist/main/` folder, not only `main.exe`.

At minimum, keep these together:

- `main.exe`
- `app_settings.json`
- `config.json`
- `db_config.json`
- `site/`
- `picture/`

## Suggested Field Test Workflow

Before copying to the test PC:

1. Set `app_settings.json`
   Example:
   ```json
   {
     "site_profile": "company"
   }
   ```

2. Set `config.json`
   Example:
   ```json
   {
     "MIR_IP": "http://10.11.202.251",
     "heartbeat_display_count": 6
   }
   ```

3. Set `db_config.json`
   Example:
   ```json
   {
     "host": "192.168.1.10",
     "port": 5432,
     "database": "military_mir250_project",
     "user": "postgres",
     "password": "123456"
   }
   ```

4. Copy the full `dist/main/` folder to the target PC.

5. On the target PC, edit only the JSON files if IP, site, or DB endpoint changes.

## Important Deployment Note

This application still requires reachable dependencies at runtime:

- MiR robot API
- PostgreSQL database

Packaging only solves Python dependency delivery. It does not embed a PostgreSQL server.

If the target PC does not have local PostgreSQL, point `db_config.json` to a reachable database server instead of `localhost`.
