"""English translations."""

STRINGS = {
    # -------- Header --------
    "logo_sub": "Multi-Protocol Tunnel Manager v3.0",
    "logo_proto": "TCP | KCP | QUIC | WebSocket + HAProxy Multi-Server",

    # -------- Generic prompts --------
    "choose": "Choose an option",
    "invalid": "Invalid choice!",
    "press_enter": "Press Enter to return...",
    "cancel": "Cancelled.",
    "yes": "Yes",
    "no": "No",
    "back": "Back",
    "continue_q": "Continue?",
    "confirm_delete": "Are you sure you want to delete?",

    # -------- Header labels --------
    "hdr_location": "Server location",
    "hdr_frp_version": "FRP version",
    "hdr_nodes": "Nodes",
    "hdr_routes": "Routes",
    "hdr_channels": "Channels",
    "hdr_not_installed": "not installed",
    "hdr_up_to_date": "(up to date)",

    # -------- Menu items --------
    "menu_install": "Install / Update FRP + HAProxy",
    "menu_nodes": "Manage Nodes (foreign servers)",
    "menu_simple_route": "Create Simple Route",
    "menu_balanced_route": "Create Balanced Route",
    "menu_manage_routes": "Manage Routes & Channels",
    "menu_export": "Export",
    "menu_import": "Import",
    "menu_health": "Health Check",
    "menu_speedtest": "Speedtest",
    "menu_optimize": "Optimize System (BBR / UDP)",
    "menu_backup": "Backup / Restore State",
    "menu_reset": "Reset",
    "menu_lang": "Language",
    "menu_help": "Dastyar",
    "menu_help_toggle": "Help Mode",
    "menu_uninstall": "Uninstall",
    "menu_switch": "Switch Location (Iran \u2194 Kharej)",
    "menu_exit": "Exit",
    "menu_tip": "tip: press the number and Enter",
    "help_hint_line": "For help on this menu, press [h]",

    # -------- Menu hints --------
    "hint_menu_install": "Install / update FRP + HAProxy",
    "hint_menu_nodes": "Add / edit / delete foreign servers",
    "hint_menu_simple_route": "1 channel → one node (no HAProxy)",
    "hint_menu_balanced_route": "N channels + HAProxy (higher bandwidth)",
    "hint_menu_manage_routes": "View / edit routes and channels",
    "hint_menu_export": "Export channel config for a node",
    "hint_menu_import": "Load Hub compact on this node",
    "hint_menu_haproxy": "Manage HAProxy (rebuild / restart / logs)",
    "hint_menu_health": "Check health of channels and routes",
    "hint_menu_speedtest": "iperf3 speedtest on one channel",
    "hint_menu_optimize": "Tune system for higher bandwidth",
    "hint_menu_backup": "Backup / restore state and configs",
    "hint_menu_reset": "Delete everything (destructive)",
    "hint_menu_lang": "Change UI language",
    "hint_menu_help": "Show full help",
    "hint_menu_help_toggle": "Toggle inline hints under menu items",
    "hint_menu_wizard": "Full wizard: create Node + Route in one flow",

    # -------- Help toggle --------
    "help_toggle_on": "Help Mode: ON",
    "help_toggle_off": "Help Mode: OFF",

    # -------- Advisor --------
    "adv_action_required": "Action Required",
    "adv_frp_missing_1": "FRP binary is not installed.",
    "adv_frp_missing_2": "Step 1 → Use menu [1] to install FRP v{v}.",
    "adv_frp_missing_3": "Everything else depends on this.",

    "adv_no_nodes": "No nodes yet → add one from [2]",
    "adv_no_routes": "Nodes exist, but no routes yet",
    "adv_create_route": "→ Create from [3] (Simple) or [4] (Balanced)",
    "adv_all_ok": "All good",
    "adv_can_create": "→ New route: [3] or [4]",

    "adv_kharej_no_channels": "No channels yet",
    "adv_kharej_get_compact": "→ Get compact from Hub, then import via [7]",
    "adv_kharej_channels_ok": "{n} channel(s) — {state}",
    "adv_kharej_no_service": "No local service on target ports",
    "adv_kharej_start_service": "→ Start Xray/service on target ports",
    "adv_kharej_all_service_ok": "Local service is listening on all ports",

    # -------- Nodes menu --------
    "nodes_header": "Nodes",
    "nodes_no": "No nodes configured yet.",
    "nodes_add": "Add node",
    "nodes_edit": "Edit node",
    "nodes_remove": "Remove node (deletes its channels)",
    "nodes_name": "Node name (e.g. hetzner, walter)",
    "nodes_name_invalid": "Invalid name. Use a-z, 0-9, dash (2-32 chars).",
    "nodes_exists": "Node '{n}' already exists.",
    "nodes_host": "Host (IP or domain)",
    "nodes_location": "Location (optional)",
    "nodes_note": "Note (optional)",
    "nodes_added": "Node '{n}' added.",
    "nodes_updated": "Node '{n}' updated.",
    "nodes_removed": "Node '{n}' removed. {c} channel(s) deleted.",
    "nodes_select": "Select node",
    "nodes_select_del": "Select node to remove",

    # -------- Simple Route --------
    "sr_title": "Create Simple Route",
    "sr_no_nodes": "You need to add a node first (menu [2]).",
    "sr_select_node": "Select target node",
    "sr_entry_port": "Entry Port (public port on Hub, e.g. 8443)",
    "sr_target_port": "Target Port (service on Node, e.g. 8443)",
    "sr_protocol": "Protocol",
    "sr_will_create": "Will create one channel: :{entry} → {node}:{target} ({proto})",
    "sr_created": "Simple Route created!",
    "sr_created_channel": "Channel: {name}",

    # -------- Balanced Route --------
    "br_title": "Create Balanced Route",
    "br_no_nodes": "You need to add a node first (menu [2]).",
    "br_entry_port": "Entry Port (public port on Hub, e.g. 443)",
    "br_select_nodes": "Select node(s) (multi)",
    "br_channels_per_node": "Channels per node?",
    "br_channel_protos": "Protocols (e.g. tcp,tcp,ws)",
    "br_will_create": "Will create {n} channels across {c} node(s)",
    "br_created": "Balanced Route created!",
    "br_haproxy_rebuilt": "HAProxy rebuilt with {n} channels.",

    # -------- Manage Routes --------
    "mr_title": "Manage Routes",
    "mr_no_routes": "No routes exist yet.",
    "mr_select": "Select route",
    "mr_deleted": "Route '{r}' removed ({n} channels).",

    # -------- Export/Import --------
    "export_no_nodes": "No nodes.",
    "export_which_node": "Which node?",
    "export_no_channels": "No channels for this node.",
    "export_done": "Exported to:",
    "export_hint": "Copy the file and paste on the node via menu [7].",

    "import_hub_warn": "Import runs on the NODE (Kharej) only.",
    "import_paste_hint": "Paste compact lines. Empty line to finish.",
    "import_no_lines": "No valid lines.",
    "import_node_missing": "Node '{n}' not defined locally.",
    "import_hub_host": "Hub host (Iran server IP)",
    "import_done": "Imported {n} channels.",

    # -------- HAProxy --------
    "hap_invalid": "HAProxy config invalid:",

    # -------- Health --------
    "health_no_tunnels": "No channels.",

    # -------- Speedtest --------
    "speed_no_tunnels": "No channels.",
    "speed_select": "Select channel",
    "speed_mode_srv": "Server mode (run on Kharej)",
    "speed_mode_cli": "Client test (run on Iran)",
    "speed_mode": "Mode",
    "speed_starting_srv": "Starting iperf3 server on :{p} (CTRL+C to stop)",
    "speed_duration": "Duration (sec)",
    "speed_testing": "Testing through {name}...",
    "speed_throughput": "Throughput: {m} Mbps",
    "speed_failed": "Failed: {e}",

    # -------- Optimize --------
    "opt_tcp": "TCP/BBR",
    "opt_udp": "UDP",
    "opt_all": "Both + limits",
    "opt_tcp_done": "TCP tuned.",
    "opt_udp_done": "UDP tuned.",
    "opt_all_done": "All tuned.",

    # -------- Reset --------
    "reset_warning": "DESTRUCTIVE OPERATIONS BELOW",
    "reset_all_tunnels": "Delete all routes and channels",
    "reset_haproxy_only": "Remove HAProxy only",
    "reset_full": "Full reset (routes + HAProxy + state)",
    "reset_all_tunnels_q": "Delete ALL routes and channels?",
    "reset_all_done": "All removed.",
    "reset_haproxy_done": "HAProxy removed.",
    "reset_full_q": "FULL RESET? All data will be lost.",
    "reset_full_done": "Full reset done.",

    # -------- Backup --------
    "bak_create": "Create backup",
    "bak_restore": "Restore latest backup",
    "bak_list": "List backups",
    "bak_saved": "Backup saved: {p}",
    "bak_none": "No backups.",
    "bak_restore_q": "Restore?",
    "bak_restored": "Restored.",

    # -------- Install --------
    "install_title": "Install / Update FRP",
    "install_already_q": "FRP already installed. Re-download?",
    "install_ready": "FRP ready — installed v{v}",
    "install_failed": "frps binary still not found!",

    # -------- Language --------
    "lang_current": "Current language",
    "lang_set": "Language set to {lang}",

# -------- Wizard --------
"wiz_title": "Combined Wizard (Node + Route)",
"wiz_intro_1": "This wizard creates in one flow:",
"wiz_intro_2": "  1. A Node (Kharej server)",
"wiz_intro_3": "  2. A Route (public port on Hub)",
"wiz_intro_4": "  3. All channels in between",
"wiz_choose_mode": "Wizard mode:",
"wiz_quick": "Quick — 3 questions, rest auto (recommended)",
"wiz_custom": "Custom — full control over everything",
"wiz_cancel": "0 Cancel",
"wiz_step": "Step {n}/{total}",
"wiz_step_node": "Configure Node (Kharej server)",
"wiz_step_route": "Configure Route (public port on Hub)",
"wiz_step_review": "Review and confirm",
"wiz_node_name": "Node name",
"wiz_node_host": "Node host (IP or domain)",
"wiz_node_location": "Location (optional)",
"wiz_node_note": "Note (optional)",
"wiz_entry_port": "Entry port (public on Hub)",
"wiz_target_port": "Target port (service on {node})",
"wiz_protocol": "Protocol",
"wiz_route_mode": "Route mode",
"wiz_mode_simple": "Simple — 1 channel, no HAProxy",
"wiz_mode_balanced": "Balanced — N channels + HAProxy",
"wiz_review": "Review — the following will be created:",
"wiz_create_confirm": "Create this route?",
"wiz_success": "Setup complete!",
"wiz_next_1": "Export config for this node:",
"wiz_next_2": "Import on the node:",
"wiz_next_3": "Start service on the node:",
"wiz_created_node": "Node: {name}",
"wiz_created_route": "Route: {id}",
"wiz_created_channels": "Channels: {n}",
"wiz_online_all": "All {n} channels ONLINE",
"wiz_online_partial": "{online}/{total} channels online",

# -------- Extra hints --------
"hint_menu_wizard": "Full wizard: create Node + Route in one flow",
"hint_uninstall": "Remove FRP Manager (multiple levels)",
"hint_show_ip": "Toggle display of public IP",


    "menu_wizard": "Wizard",
    "menu_channels": "Channels",
    "menu_show_ip": "Show IP",
}
