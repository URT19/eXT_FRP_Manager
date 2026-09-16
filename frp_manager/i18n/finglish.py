"""Finglish (Persian in Latin script) translations."""

STRINGS = {
    # -------- Header --------
    "logo_sub": "Modiriyat Tunnel Multi-Protocol v3.0",
    "logo_proto": "TCP | KCP | QUIC | WebSocket + HAProxy Multi-Server",

    # -------- Generic prompts --------
    "choose": "Yek gozine entekhab kon",
    "invalid": "Gozine eshtebah!",
    "press_enter": "Enter bezan baraye bargasht...",
    "cancel": "Cancel shod.",
    "yes": "Bale",
    "no": "Na",
    "back": "Bargasht",
    "continue_q": "Edame midi?",
    "confirm_delete": "Motmaeni ke mikhay pak koni?",

    # -------- Header labels --------
    "hdr_location": "Server location",
    "hdr_frp_version": "FRP version",
    "hdr_nodes": "Node-ha",
    "hdr_routes": "Route-ha",
    "hdr_channels": "Channel-ha",
    "hdr_not_installed": "nasb nashode",
    "hdr_up_to_date": "(up to date)",

    # -------- Menu items --------
    "menu_install": "Nasb / Update FRP + HAProxy",
    "menu_nodes": "Modiriyat Node-ha",
    "menu_simple_route": "Sakht Simple Route",
    "menu_balanced_route": "Sakht Balanced Route",
    "menu_manage_routes": "Modiriyat Route-ha",
    "menu_export": "Export baraye Node",
    "menu_import": "Import rooye Node",
    "menu_health": "Health Check",
    "menu_speedtest": "Speedtest",
    "menu_optimize": "Optimize System (BBR / UDP)",
    "menu_backup": "Backup / Restore State",
    "menu_reset": "Reset",
    "menu_lang": "Zaban",
    "menu_help": "Dastyar",
    "menu_help_toggle": "Help Mode",
    "menu_uninstall": "Uninstall",
    "menu_switch": "Switch Location (Iran \u2194 Kharej)",
    "menu_exit": "Khoroj",
    "menu_tip": "tip: shomare ra bezan va Enter",
    "help_hint_line": "Baraye help-e in menu, [h] bezan",

    # -------- Menu hints --------
    "hint_menu_install": "FRP + HAProxy ra nasb ya update kon",
    "hint_menu_nodes": "Server-haye kharej ra add/edit/delete kon",
    "hint_menu_simple_route": "1 channel → yek node (bedoone HAProxy)",
    "hint_menu_balanced_route": "N channel + HAProxy (bandwidth bala)",
    "hint_menu_manage_routes": "Route-ha va channel-ha ra bebin/edit kon",
    "hint_menu_export": "Config-e channel-ha ra baraye node export kon",
    "hint_menu_import": "Compact-e HUB ra rooye in node load kon",
    "hint_menu_haproxy": "HAProxy ra manage kon (rebuild/restart/log)",
    "hint_menu_health": "Salamat-e channel-ha va route-ha ra check kon",
    "hint_menu_speedtest": "iperf3 speedtest rooye yek channel",
    "hint_menu_optimize": "System ro baraye bandwidth-e bala tune kon",
    "hint_menu_backup": "State va config-ha ra save/restore kon",
    "hint_menu_reset": "Hame chi ra pak kon (khatarnaak)",
    "hint_menu_lang": "Zaban-e UI ra avaz kon",
    "hint_menu_help": "Rahnama-ye kamel ra bebin",
    "hint_menu_help_toggle": "Tozih-ha-ye ziresh menu-ha ro roshan/khamoosh kon",
    "hint_menu_wizard": "Wizard-e kamel: Node + Route ba yek bar",

    # -------- Help toggle --------
    "help_toggle_on": "Help Mode: ROSHAN",
    "help_toggle_off": "Help Mode: KHAMOOSH",

    # -------- Advisor --------
    "adv_action_required": "Eghdam Lazem",
    "adv_frp_missing_1": "FRP binary nasb nashode.",
    "adv_frp_missing_2": "Ghadam 1 → az menu [1] FRP v{v} ro nasb kon.",
    "adv_frp_missing_3": "Hame chiz be in ghadam vabaste ast.",

    "adv_no_nodes": "Hich node-i nazashti → az [2] add kon",
    "adv_no_routes": "Node-haye mojood, vali hanooz route nasakhti",
    "adv_create_route": "→ Az [3] (Simple) ya [4] (Balanced) route besaz",
    "adv_all_ok": "Hame chi OK",
    "adv_can_create": "→ Baraye route-e jadid: [3] ya [4]",

    "adv_kharej_no_channels": "Hanooz channel nadari",
    "adv_kharej_get_compact": "→ Compact az HUB (Iran) begir, bad az [7] import kon",
    "adv_kharej_channels_ok": "{n} channel — {state}",
    "adv_kharej_no_service": "Service rooye port-ha peyda nashod",
    "adv_kharej_start_service": "→ Xray/service rooye port-ha start kon",
    "adv_kharej_all_service_ok": "Service rooye hame port-ha listen mikone",

    # -------- Nodes menu --------
    "nodes_header": "Node-ha",
    "nodes_no": "Hich node-i tarif nashode.",
    "nodes_add": "Add node",
    "nodes_edit": "Edit node",
    "nodes_remove": "Remove node (channel-hash ham pak mishan)",
    "nodes_name": "Esm-e node (mesal: hetzner, walter)",
    "nodes_name_invalid": "Esm na-motabar. faghat a-z, 0-9, dash (2-32 char).",
    "nodes_exists": "Node '{n}' ghablan vojud dare.",
    "nodes_host": "Host (IP ya domain)",
    "nodes_location": "Location (ekhtiari)",
    "nodes_note": "Note (ekhtiari)",
    "nodes_added": "Node '{n}' add shod.",
    "nodes_updated": "Node '{n}' update shod.",
    "nodes_removed": "Node '{n}' pak shod. {c} channel ham pak shodan.",
    "nodes_select": "Node ra entekhab kon",
    "nodes_select_del": "Node mored nazar baraye delete",

    # -------- Simple Route --------
    "sr_title": "Sakht Simple Route",
    "sr_no_nodes": "Aval bayad node add koni (menu [2]).",
    "sr_select_node": "Node-e maqsad ra entekhab kon",
    "sr_entry_port": "Entry Port (port-e public rooye HUB, mesal 8443)",
    "sr_target_port": "Target Port (service rooye NODE, mesal 8443)",
    "sr_protocol": "Protocol",
    "sr_will_create": "Yek channel sakhte mishe: :{entry} → {node}:{target} ({proto})",
    "sr_created": "Simple Route sakhte shod!",
    "sr_created_channel": "Channel: {name}",

    # -------- Balanced Route --------
    "br_title": "Sakht Balanced Route",
    "br_no_nodes": "Aval bayad node add koni (menu [2]).",
    "br_entry_port": "Entry Port (port-e public rooye HUB, mesal 443)",
    "br_select_nodes": "Node-ha ra entekhab kon (chand-ta)",
    "br_channels_per_node": "Chand channel per node?",
    "br_channel_protos": "Protocol-ha (misal: tcp,tcp,ws)",
    "br_will_create": "{n} channel baraye {c} node sakhte mishe",
    "br_created": "Balanced Route sakhte shod!",
    "br_haproxy_rebuilt": "HAProxy rebuild shod ba {n} channel.",

    # -------- Manage Routes --------
    "mr_title": "Modiriyat Route-ha",
    "mr_no_routes": "Hich route-i vojood nadare.",
    "mr_select": "Route ra entekhab kon",
    "mr_deleted": "Route '{r}' pak shod ({n} channel).",

    # -------- Export/Import --------
    "export_no_nodes": "Hich node-i nadari.",
    "export_which_node": "Kodoom node?",
    "export_no_channels": "Hich channel-i baraye in node nadari.",
    "export_done": "Export shod be:",
    "export_hint": "File ra copy kon, rooye node az menu [7] paste kon.",

    "import_hub_warn": "Import faghat rooye NODE (Kharej) anjam mishe.",
    "import_paste_hint": "Line-haye compact ra paste kon. Line khali = payan.",
    "import_no_lines": "Hich line motabar-i nabood.",
    "import_node_missing": "Node '{n}' rooye in server tarif nashode.",
    "import_hub_host": "Host-e HUB (IP-e server Iran)",
    "import_done": "{n} channel import shod.",

    # -------- HAProxy --------
    "hap_invalid": "HAProxy config na-motabar:",

    # -------- Health --------
    "health_no_tunnels": "Hich channel-i nadari.",

    # -------- Speedtest --------
    "speed_no_tunnels": "Hich channel-i nadari.",
    "speed_select": "Channel ra entekhab kon",
    "speed_mode_srv": "Server mode (rooye Kharej ejra kon)",
    "speed_mode_cli": "Client test (rooye Iran ejra kon)",
    "speed_mode": "Mode",
    "speed_starting_srv": "Starting iperf3 server rooye :{p} (CTRL+C = stop)",
    "speed_duration": "Moddat (sec)",
    "speed_testing": "Testing az {name}...",
    "speed_throughput": "Throughput: {m} Mbps",
    "speed_failed": "Fail shod: {e}",

    # -------- Optimize --------
    "opt_tcp": "TCP/BBR",
    "opt_udp": "UDP",
    "opt_all": "Harf-e (Both) + limits",
    "opt_tcp_done": "TCP tune shod.",
    "opt_udp_done": "UDP tune shod.",
    "opt_all_done": "Hame tune shod.",

    # -------- Reset --------
    "reset_warning": "EGHDAAM-E KHATARNAAK — PAK KARDAN",
    "reset_all_tunnels": "Pak kardan-e hame route-ha va channel-ha",
    "reset_haproxy_only": "Faghat HAProxy ro pak kon",
    "reset_full": "Full reset (route-ha + HAProxy + state)",
    "reset_all_tunnels_q": "Hame route-ha va channel-ha pak beshan?",
    "reset_all_done": "Hame pak shodan.",
    "reset_haproxy_done": "HAProxy pak shod.",
    "reset_full_q": "FULL RESET? Hame data az dast mire.",
    "reset_full_done": "Full reset anjam shod.",

    # -------- Backup --------
    "bak_create": "Sakht-e backup",
    "bak_restore": "Restore-e akharin backup",
    "bak_list": "List-e backup-ha",
    "bak_saved": "Backup save shod: {p}",
    "bak_none": "Hich backup-i nist.",
    "bak_restore_q": "Restore konam?",
    "bak_restored": "Restore shod.",

    # -------- Install --------
    "install_title": "Nasb / Update FRP",
    "install_already_q": "FRP ghablan nasbe. Dobare download konam?",
    "install_ready": "FRP amade — nasb shode v{v}",
    "install_failed": "frps binary peyda nashod!",

    # -------- Language --------
    "lang_current": "Zaban-e feli",
    "lang_set": "Zaban shod {lang}",

# -------- Wizard --------
"wiz_title": "Wizard-e Tarkibi (Node + Route)",
"wiz_intro_1": "In wizard dar yek jaryan misaze:",
"wiz_intro_2": "  1. Node (server kharej)",
"wiz_intro_3": "  2. Route (port public rooye HUB)",
"wiz_intro_4": "  3. Channel-ha (tunnel-ha)",
"wiz_choose_mode": "Wizard mode:",
"wiz_quick": "Quick — 3 so'al, baghie auto (pishnahad)",
"wiz_custom": "Custom — kontrol-e kamel rooye hame chiz",
"wiz_cancel": "0 Cancel",
"wiz_step": "Step {n}/{total}",
"wiz_step_node": "Tanzim-e Node (server kharej)",
"wiz_step_route": "Tanzim-e Route (port public rooye HUB)",
"wiz_step_review": "Bazbini va tasdiq",
"wiz_node_name": "Esm-e node",
"wiz_node_host": "Host-e node (IP ya domain)",
"wiz_node_location": "Location (ekhtiari)",
"wiz_node_note": "Note (ekhtiari)",
"wiz_entry_port": "Entry port (public rooye HUB)",
"wiz_target_port": "Target port (service rooye {node})",
"wiz_protocol": "Protocol",
"wiz_route_mode": "Route mode",
"wiz_mode_simple": "Simple — 1 channel, bedoone HAProxy",
"wiz_mode_balanced": "Balanced — N channel + HAProxy",
"wiz_review": "Review — in chiz-ha sakhte mishan:",
"wiz_create_confirm": "In route sakhte beshe?",
"wiz_success": "Setup kamel shod!",
"wiz_next_1": "Config ra baraye node export kon:",
"wiz_next_2": "Rooye node import kon:",
"wiz_next_3": "Service rooye node start kon:",
"wiz_created_node": "Node: {name}",
"wiz_created_route": "Route: {id}",
"wiz_created_channels": "Channel-ha: {n}",
"wiz_online_all": "Hame {n} channel ONLINE",
"wiz_online_partial": "{online}/{total} channel online",

# -------- Extra hints --------
"hint_menu_wizard": "Wizard-e kamel: Node + Route ba yek bar",
"hint_uninstall": "Pak kardan-e FRP Manager (chand level)",
"hint_show_ip": "Neshoon/makhfi kardan-e IP-e public",


    "menu_wizard": "Wizard",
    "menu_channels": "Modiriyat Channel-ha",
    "menu_show_ip": "Show IP",
}
