# Reminor Desktop App - Tauri Implementation Plan

## Overview

Transform Reminor from a Docker-only web application into a **standalone desktop app** using [Tauri 2.x](https://tauri.app/). The user downloads a single installer, runs it, and the app works out of the box — no Docker, no Python installation, no terminal commands.

**Architecture:** Tauri (Rust + Svelte webview) launches the Python backend as a **PyInstaller sidecar** process. The frontend talks to the backend via HTTP on localhost, exactly like the current setup — but everything runs inside a single app.

```
┌─────────────────────────────────────────────┐
│  Tauri Desktop App                          │
│  ┌───────────────────────────────────────┐  │
│  │  Svelte Frontend (WebView)            │  │
│  │  Same UI, same code                   │  │
│  └──────────────┬────────────────────────┘  │
│                 │ HTTP (localhost:18923)      │
│  ┌──────────────▼────────────────────────┐  │
│  │  Python Backend (PyInstaller sidecar) │  │
│  │  FastAPI + Memvid + Embeddings        │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

### Key Decisions

| Decision | Choice |
|----------|--------|
| Auth model | **Single-user** with optional password (no registration, no multi-user JWT) |
| Backend packaging | **PyInstaller** single executable (~500MB) |
| Target platforms | **Linux** (AppImage) + **Windows** (NSIS installer) |
| Embedding model | Downloaded on **first launch** (~300MB), not bundled in installer |
| Data directory | `~/.reminor/` (Linux) or `%APPDATA%/reminor/` (Windows) |
| Backend port | `127.0.0.1:18923` (fixed, localhost only) |
| Docker version | **Unchanged** — all backend changes are behind a `DESKTOP_MODE` flag |

---

## Directory Structure

```
reminor/
├── backend/                        # EXISTING (minor changes)
│   ├── api/
│   │   ├── main.py                 # + desktop mode detection, desktop endpoints
│   │   └── auth_routes.py          # + desktop login endpoint
│   └── core/
│       ├── auth.py                 # + desktop user bypass
│       └── ...
├── reminor-frontend/               # EXISTING (minor changes)
│   ├── src/
│   │   ├── lib/
│   │   │   ├── api.js              # + Tauri detection for API_BASE
│   │   │   ├── auth.js             # + desktop auto-auth flow
│   │   │   ├── stores.js           # + desktopMode store
│   │   │   ├── i18n.js             # + setup wizard translations
│   │   │   └── pages/
│   │   │       ├── Login.svelte    # + hide registration in desktop
│   │   │       └── Setup.svelte    # NEW: first-run wizard
│   │   └── App.svelte              # + setup page routing
│   └── vite.config.js              # + Tauri dev server config
│
├── src-tauri/                      # NEW — Tauri shell (Rust)
│   ├── Cargo.toml
│   ├── tauri.conf.json
│   ├── capabilities/default.json
│   ├── build.rs
│   ├── icons/
│   ├── sidecars/                   # PyInstaller output (at build time)
│   └── src/
│       ├── main.rs
│       └── lib.rs                  # Sidecar management, health check
│
├── desktop/                        # NEW — Build tooling
│   └── pyinstaller/
│       ├── desktop_main.py         # Desktop entry point for PyInstaller
│       ├── reminor_backend.spec    # PyInstaller spec file
│       ├── build_sidecar.sh        # Linux build script
│       └── build_sidecar.ps1       # Windows build script
│
├── docker-compose.prod.yml         # UNCHANGED
├── Dockerfile.prod                 # UNCHANGED
└── Caddyfile                       # UNCHANGED
```

---

## Phase 1: Backend — Desktop Mode

All changes are conditional on `REMINOR_DESKTOP_MODE=1` environment variable. When not set, the backend behaves exactly as today.

### 1.1 `backend/core/auth.py` — Desktop Auth Bypass

**Problem:** Every API endpoint uses `get_current_user()` which requires a valid JWT token. In desktop mode, there's only one user and no login flow.

**Solution:** When `DESKTOP_MODE` is active, `get_current_user()` returns a fixed desktop user without validating any token.

```python
DESKTOP_MODE = os.getenv("REMINOR_DESKTOP_MODE", "0") == "1"

async def get_current_user(credentials=Depends(bearer_scheme)) -> CurrentUser:
    if DESKTOP_MODE:
        return _get_desktop_user()
    # ... existing JWT validation (unchanged) ...

def _get_desktop_user() -> CurrentUser:
    config = _load_desktop_config()  # reads ~/.reminor/config.json
    return CurrentUser(
        user_id="desktop-user",
        email="desktop@localhost",
        name=config.get("name", "User"),
        language=config.get("language", "it"),
    )
```

**Note:** The `JWT_SECRET_KEY` RuntimeError at module load (line 22-27) is handled by `desktop_main.py` which auto-generates and sets it before importing the module.

### 1.2 `backend/api/main.py` — Desktop Endpoints

Add `DESKTOP_MODE` flag and override `DATA_DIR` from environment:

```python
DESKTOP_MODE = os.getenv("REMINOR_DESKTOP_MODE", "0") == "1"

if os.getenv("REMINOR_DATA_DIR"):
    DATA_DIR = Path(os.getenv("REMINOR_DATA_DIR"))
```

New endpoints (only respond when `DESKTOP_MODE=1`):

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/desktop/status` | GET | Returns `{first_run, model_downloaded}` |
| `/desktop/setup` | POST | Saves first-run config (name, language, password) |
| `/desktop/model-status` | GET | Checks embedding model download state |
| `/auth/desktop-login` | POST | Validates optional password, returns token |

### 1.3 `desktop/pyinstaller/desktop_main.py` — Desktop Entry Point

This is the PyInstaller entry point that bootstraps everything before importing FastAPI:

```python
def main():
    # 1. Set REMINOR_DESKTOP_MODE=1
    # 2. Resolve data dir (~/.reminor/data/)
    # 3. Auto-generate JWT_SECRET_KEY, persist to ~/.reminor/config.json
    # 4. Set HF_HOME to ~/.reminor/models/ (for embedding model cache)
    # 5. Configure sys.path for PyInstaller bundle
    # 6. Launch: uvicorn backend.api.main:app --host 127.0.0.1 --port 18923
```

Order matters: env vars must be set **before** Python imports `auth.py` (which reads `JWT_SECRET_KEY` at module level).

---

## Phase 2: Frontend — Tauri Detection

### 2.1 `reminor-frontend/src/lib/api.js` — API Base URL

```javascript
export const isTauri = Boolean(window.__TAURI_INTERNALS__);
const isDev = !isTauri && (window.location.hostname === 'localhost' || ...);
const API_BASE = isTauri
    ? 'http://127.0.0.1:18923'     // Tauri desktop
    : isDev
        ? 'http://127.0.0.1:8000'  // Dev server
        : '';                        // Docker production
```

### 2.2 `reminor-frontend/src/lib/auth.js` — Desktop Auto-Auth

In `initAuth()`, detect Tauri and take the desktop path:

```javascript
if (isTauri) {
    const status = await fetch(`${API_BASE}/desktop/status`);
    if (status.first_run)  → navigate to Setup wizard
    if (status.has_password) → show password-only Login
    else → auto-login via POST /auth/desktop-login (no password needed)
}
```

### 2.3 `Setup.svelte` — First-Run Wizard (New Page)

Retro terminal aesthetic matching the existing UI. Steps:

```
┌─────────────────────────────────────────┐
│  > REMINOR DESKTOP v2.0                 │
│  > FIRST RUN CONFIGURATION              │
│                                         │
│  1. LANGUAGE .............. [IT] [EN]   │
│  2. NAME .................. [________]  │
│  3. PASSWORD (optional) ... [________]  │
│                                         │
│  > DOWNLOADING AI MODEL... 67% ████░░   │
│                                         │
│  [COMPLETE SETUP]                       │
└─────────────────────────────────────────┘
```

Model download progress is shown by polling `GET /desktop/model-status` which checks the HuggingFace cache directory for the `unsloth/embeddinggemma-300m` model files.

### 2.4 `Login.svelte` — Desktop Simplification

When `isTauri` is true:
- Hide registration toggle and email field
- Show only password field
- Header: "REMINOR DESKTOP" instead of boot sequence
- Submit calls `/auth/desktop-login` instead of `/auth/login`

### 2.5 `vite.config.js` — Tauri Dev Server

```javascript
export default defineConfig({
    plugins: [svelte()],
    server: {
        port: 1420,        // Tauri expects this port
        strictPort: true,
    },
    envPrefix: ['VITE_', 'TAURI_'],
})
```

### 2.6 `i18n.js` — Setup Translations

New keys for IT/EN:
- `setup.welcome`, `setup.language`, `setup.name`
- `setup.password_optional`, `setup.password_hint`
- `setup.downloading_model`, `setup.model_progress`
- `setup.complete`, `setup.start`

---

## Phase 3: Tauri Shell (Rust)

### 3.1 `src-tauri/Cargo.toml`

```toml
[package]
name = "reminor"
version = "0.1.0"
edition = "2021"

[dependencies]
tauri = { version = "2", features = [] }
tauri-plugin-shell = "2"
tauri-plugin-process = "2"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
reqwest = { version = "0.12", features = ["blocking"] }
dirs = "5"

[build-dependencies]
tauri-build = { version = "2", features = [] }
```

### 3.2 `src-tauri/tauri.conf.json`

Key configuration:

```json
{
    "build": {
        "frontendDist": "../reminor-frontend/dist",
        "devUrl": "http://localhost:1420",
        "beforeBuildCommand": "cd reminor-frontend && npm run build"
    },
    "app": {
        "windows": [{
            "title": "REMINOR",
            "width": 1024, "height": 768,
            "visible": false
        }],
        "security": {
            "csp": "... connect-src http://127.0.0.1:18923 ..."
        }
    },
    "bundle": {
        "targets": ["appimage", "nsis"],
        "resources": ["sidecars/reminor-backend*"]
    }
}
```

Window starts **hidden** (`visible: false`) and is shown only after the backend health check passes.

### 3.3 `src-tauri/src/lib.rs` — Core Logic

```
App Startup:
  1. Create ~/.reminor/{data, models, logs}/
  2. Resolve sidecar path (from bundle resources)
  3. Spawn: reminor-backend with env vars
     - REMINOR_DESKTOP_MODE=1
     - REMINOR_DATA_DIR=~/.reminor/data
     - HF_HOME=~/.reminor/models
  4. Redirect sidecar stdout/stderr → ~/.reminor/logs/backend.log
  5. Poll http://127.0.0.1:18923/health every 1s
     - Timeout: 300s (5 min, for first-run model download)
  6. When healthy → show main window

App Shutdown:
  - Kill sidecar process (SIGTERM → wait → SIGKILL)
```

### 3.4 `src-tauri/capabilities/default.json`

```json
{
    "identifier": "default",
    "windows": ["main"],
    "permissions": [
        "core:default",
        "shell:allow-open",
        "shell:allow-execute",
        "shell:allow-spawn",
        "process:allow-exit"
    ]
}
```

---

## Phase 4: PyInstaller Configuration

### 4.1 `desktop/pyinstaller/reminor_backend.spec`

```python
a = Analysis(
    ['desktop_main.py'],
    pathex=['../..'],                    # Project root
    datas=[
        ('../../backend', 'backend'),
        ('../../memvid_memory.py', '.'),
        ('../../enhanced_emotions_analyzer.py', '.'),
    ],
    hiddenimports=[
        'uvicorn', 'uvicorn.logging', 'uvicorn.loops.auto',
        'uvicorn.protocols.http.auto', 'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan.on',
        'fastapi', 'pydantic', 'email_validator',
        'jose', 'jose.jwt', 'bcrypt',
        'litellm', 'memvid_sdk', 'sentence_transformers',
        'torch', 'numpy', 'dotenv', 'multipart',
    ],
    excludes=['tkinter', 'matplotlib', 'PIL', 'scipy', 'pandas'],
)

exe = EXE(pyz, a.scripts, a.binaries, a.datas, [],
    name='reminor-backend',
    console=False,     # No console window on Windows
    upx=True,
)
```

### 4.2 Build Scripts

**Linux/macOS** (`desktop/pyinstaller/build_sidecar.sh`):
```bash
#!/bin/bash
# 1. Create venv with Python 3.11
# 2. pip install torch (CPU-only) + requirements.txt + pyinstaller
# 3. pyinstaller --clean reminor_backend.spec
# 4. Copy dist/reminor-backend → src-tauri/sidecars/
```

**Windows** (`desktop/pyinstaller/build_sidecar.ps1`):
```powershell
# Same steps but for Windows environment
# Output: reminor-backend.exe
```

---

## Phase 5: Build & Development

### Development Workflow

```bash
# Terminal 1 — Python backend in desktop mode
REMINOR_DESKTOP_MODE=1 \
REMINOR_DATA_DIR=$HOME/.reminor/data \
HF_HOME=$HOME/.reminor/models \
JWT_SECRET_KEY=dev-secret-key \
python -m uvicorn backend.api.main:app --host 127.0.0.1 --port 18923

# Terminal 2 — Tauri dev (frontend + desktop window)
cd src-tauri && cargo tauri dev
```

### Production Build

```bash
# Step 1: Build Python sidecar
./desktop/pyinstaller/build_sidecar.sh

# Step 2: Build Tauri app (auto-builds frontend via beforeBuildCommand)
cd src-tauri && cargo tauri build

# Output:
#   Linux:   target/release/bundle/appimage/reminor_0.1.0_amd64.AppImage
#   Windows: target/release/bundle/nsis/Reminor_0.1.0_x64-setup.exe
```

### Installer Size Estimates

| Component | Size |
|-----------|------|
| Tauri shell + frontend | ~10-15 MB |
| Python sidecar (PyInstaller) | ~400-600 MB |
| **Total installer** | **~500-700 MB** |
| Embedding model (first-run download) | ~300 MB |

---

## First-Run Flow

```
User launches Reminor.AppImage (or Reminor.exe)
  │
  ├─ Tauri creates ~/.reminor/{data, models, logs}/
  ├─ Tauri spawns sidecar (reminor-backend)
  │   ├─ Sidecar auto-generates JWT secret → ~/.reminor/config.json
  │   └─ Sidecar loads SentenceTransformer → downloads model (~300MB)
  │
  ├─ Tauri polls /health (waits up to 5 minutes)
  ├─ Health check passes → window becomes visible
  │
  ├─ Frontend calls GET /desktop/status → { first_run: true }
  ├─ Frontend shows Setup.svelte wizard:
  │   ├─ Language selection (IT/EN)
  │   ├─ Name (optional)
  │   ├─ Password (optional)
  │   └─ Model download progress bar (polls /desktop/model-status)
  │
  ├─ POST /desktop/setup → saves config
  └─ Redirect to Home → ready to use
```

Subsequent launches skip the setup and either auto-login (no password) or show a simple password prompt.

---

## Data Storage Layout

```
~/.reminor/                        (Linux: ~/.reminor, Windows: %APPDATA%/reminor)
├── config.json                    # JWT secret, name, language, password hash
├── data/
│   └── desktop-user/              # Single user directory
│       ├── journal/
│       │   ├── 2024-01-15.txt
│       │   └── ...
│       ├── memory.mv2             # Memvid search index
│       ├── memory.npz             # Embedding vectors
│       ├── emotions.json
│       └── user_knowledge.json
├── models/                        # HuggingFace model cache
│   └── hub/
│       └── models--unsloth--embeddinggemma-300m/
└── logs/
    └── backend.log
```

---

## Files Summary

### Modified (existing files)

| File | Changes |
|------|---------|
| `backend/core/auth.py` | Desktop mode bypass in `get_current_user`, desktop user helper |
| `backend/api/main.py` | `DESKTOP_MODE` flag, `DATA_DIR` override, 3 desktop endpoints |
| `backend/api/auth_routes.py` | `/auth/desktop-login` endpoint |
| `reminor-frontend/src/lib/api.js` | Tauri detection, `API_BASE` for port 18923 |
| `reminor-frontend/src/lib/auth.js` | Desktop auto-auth path |
| `reminor-frontend/src/lib/stores.js` | `desktopMode` store |
| `reminor-frontend/src/App.svelte` | Setup page in routing |
| `reminor-frontend/src/lib/pages/Login.svelte` | Hide registration in desktop |
| `reminor-frontend/src/lib/i18n.js` | Setup wizard translations |
| `reminor-frontend/vite.config.js` | Tauri dev server config |
| `.gitignore` | Exclude build artifacts |

### Created (new files)

| File | Purpose |
|------|---------|
| `src-tauri/Cargo.toml` | Rust project with Tauri 2.x |
| `src-tauri/tauri.conf.json` | Tauri configuration |
| `src-tauri/capabilities/default.json` | Permissions |
| `src-tauri/src/main.rs` | Rust entry point |
| `src-tauri/src/lib.rs` | Sidecar management, health check |
| `src-tauri/build.rs` | Tauri build script |
| `reminor-frontend/src/lib/pages/Setup.svelte` | First-run wizard |
| `desktop/pyinstaller/desktop_main.py` | Desktop entry point |
| `desktop/pyinstaller/reminor_backend.spec` | PyInstaller spec |
| `desktop/pyinstaller/build_sidecar.sh` | Linux build script |
| `desktop/pyinstaller/build_sidecar.ps1` | Windows build script |

---

## Prerequisites for Development

```bash
# Rust toolchain
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Tauri CLI
cargo install tauri-cli

# Node.js 20+
# Python 3.11+
# PyInstaller: pip install pyinstaller

# Linux additional deps (Ubuntu/Debian):
sudo apt install libwebkit2gtk-4.1-dev build-essential curl wget \
    libssl-dev libgtk-3-dev libayatana-appindicator3-dev librsvg2-dev
```

---

## Notes

- The **Docker version is completely unaffected**. All desktop-specific code is behind the `REMINOR_DESKTOP_MODE` environment variable, which is never set in the Docker deployment.
- The embedding model (`unsloth/embeddinggemma-300m`, ~300MB) is **not bundled** in the installer. It downloads automatically on first launch via `sentence-transformers`. This keeps the installer size reasonable (~500-700MB instead of ~1GB).
- Port `18923` was chosen as a non-standard port to minimize conflicts with other software. It's bound to `127.0.0.1` only (not accessible from the network).
- PyInstaller bundles include CPU-only PyTorch (same optimization as the Docker image) to keep the executable size manageable.
