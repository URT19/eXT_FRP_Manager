"""Entry point: CLI, TUI, or uninstall."""
import argparse


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="frp-manager",
        description="FRP Manager v3 — CLI or TUI mode",
    )
    parser.add_argument("--tui", action="store_true",
                        help="Launch the Textual TUI")
    parser.add_argument("--cli", action="store_true",
                        help="Force the classic CLI menu")
    parser.add_argument("--uninstall", action="store_true",
                        help="Open the uninstall / cleanup menu")
    args = parser.parse_args()

    # Direct uninstall mode
    if args.uninstall:
        from .ui import uninstall as uninstall_ui
        uninstall_ui.show_menu()
        return

    if args.tui:
        from .tui.app import run
        run()
        return

    if args.cli:
        from .cli import run as cli_run
        cli_run()
        return

    # Interactive choice
    print("╭──────────────────────────────────────╮")
    print("│  FRP Manager v3                      │")
    print("├──────────────────────────────────────┤")
    print("│  [1] Classic CLI  (recommended)      │")
    print("│  [2] Textual TUI  (experimental)     │")
    print("╰──────────────────────────────────────╯")
    try:
        choice = input("Choose [1]: ").strip() or "1"
    except (EOFError, KeyboardInterrupt):
        choice = "1"

    if choice == "2":
        try:
            from .tui.app import run
            run()
        except Exception as e:
            print(f"TUI failed to start: {e}")
            print("Falling back to CLI...")
            from .cli import run as cli_run
            cli_run()
    else:
        from .cli import run as cli_run
        cli_run()


if __name__ == "__main__":
    main()
