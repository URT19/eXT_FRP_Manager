# Changelog

## [3.7.0] - 2026-09-19

### Added
- Per-hub Channel Status panel with grouped summary
- Protocol breakdown per hub (TCP/KCP/QUIC/WS)
- Online/Offline counters per hub
- Routes summary per hub
- Hub Name prompt in Wizard (for IRAN side)
- Loop in Speedtest menu (return to channel selection)

### Changed
- Speedtest channel picker now shows protocol tag `[TCP]` / `[WS]` / etc.
- Cleaner hub management screens (removed redundant logo panel)

### Fixed
- Removed duplicate function definitions across `cli.py`
- Fixed `node=` → `hub=` in Wizard Channel creation
- Fixed markup rendering in help panels

---

## [3.6.0] - 2026-09-18

### Added
- Per-hub status icons: `●` all online, `◐` partial, `○` all offline
- Route counter hidden on KHAREJ side
- Sanitized all example IPs to RFC 5737 (`203.0.113.x`)

### Changed
- Menu `[3]` renamed: `Modiriyat Hub-ha`
- Counter `Nodes` → `Hubs`

### Fixed
- `TypeError` on `_show_hub_help` (arg mismatch)
- `NameError: Hub` not imported in `cli.py`

---

## [3.5.0] - 2026-09-17

### Added
- Location-aware header (Routes shown on IRAN only)
- `HubRole` enum: `iran_server` / `kharej_server`
- `ROLE_META` dict with per-role titles, colors, workflows
- Role-aware `manage_hubs` UI

### Changed
- Hub management UI differs per side (IRAN vs KHAREJ)
- Help text adapted to server role

### Fixed
- Channel Status naming for hubs

---

## [3.4.0] - 2026-09-16

### Added
- `Hub` dataclass with `role`, `type`, `routes` fields
- `_hub_channels_menu` for per-hub channel management
- Manual channel add/edit/delete on KHAREJ

### Changed
- Menu `[8]` Import now supports Smart Detection
- `hub` field replaces `node` in `Channel` model (backward compatible)

### Fixed
- Hub deletion removes all related channels
- Channel count via host IP matching

---

## [3.3.0] - 2026-09-15

### Added
- Smart Import: auto-detects `Simple` (1 channel) vs `Balanced` (N channels)
- Auto-create Hub on import if missing
- Auto-append number on name conflict (`iran-1` → `iran-1-2`)
- New compact format v3.2 with `HubName` at start of each line

### Changed
- Compact line format:
  `HubName,HubIP,ChannelName,RouteID,Index,Proto,BindPort,Token,RemotePort,TargetPort,IperfPort`

### Fixed
- Import overwrite bug (now adds new hubs instead of replacing)

---

## [3.2.1] - 2026-09-14

### Fixed
- Wizard default mode selection
- Auto-detect in Speedtest (server vs client per side)

---

## [3.2.0] - 2026-09-13

### Added
- `Hub` model replacing `Node` (backward-compat alias kept)
- Auto-migration `nodes` → `hubs` in `state.json`
- Backup before migration
- `group_channels_by_hub()` and `hub_summary()` helpers
- `ui/header.py` for consistent top panel across menus

### Changed
- `state.json` schema version 4 → 5
- `Channel.node` → `Channel.hub` (with fallback)
- All example IPs replaced with documentation ranges

### Fixed
- Broken duplicate function definitions after patches
- `sys.path` issues when running from `/root/`

---

## [3.1.0] - 2026-09-12

### Added
- Two-column menu layout
- Lock icons (`🔒`) for disabled items
- Separate Help panel (Dastyar)
- F-key shortcuts (F1–F10)
- Locked menu items for wrong server role
- Version display in header
- Improved Wizard with step-by-step prompts

### Changed
- Better Finglish/English translations
- Menu labels shortened
- Faster menu rendering

### Fixed
- Column alignment in main menu
- Overflow of long menu labels