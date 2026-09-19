"""Entry point: CLI, TUI, or uninstall."""
import argparse
import sys
import os
from pathlib import Path


def _fix_sys_path():
    """Ensure Python loads frp_manager from the correct location (/opt).

    When running as `sudo python -m frp_manager` from /root/ or any
    directory that contains an old `frp_manager/` copy, Python may
    pick up the wrong package. We detect this and fix sys.path.
    """
    # Expected install directory
    expected = Path("/opt/frp-manager")

    # Get current package file
    current = Path(__file__).resolve()
    current_root = current.parent.parent  # .../frp_manager -> ...

    if current_root != expected:
        # We're loading from the wrong place
        print(
            f"[WARN] Loading frp_manager from: {current_root}",
            file=sys.stderr,
        )
        print(
            f"[WARN] Expected: {expected}",
            file=sys.stderr,
        )
        print(
            f"[INFO] Add to sys.path: {expected}",
            file=sys.stderr,
        )
        # Prepend expected path
        if str(expected) not in sys.path:
            sys.path.insert(0, str(expected))


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="frp-manager",
        description="eXT FRP Manager - CLI or TUI mode",
    )
    parser.add_argument("--tui", action="store_true",
                        help="Launch the Textual TUI")
    parser.add_argument("--cli", action="store_true",
                        help="Force the classic CLI menu")
    parser.add_argument("--uninstall", action="store_true",
                        help="Open the uninstall / cleanup menu")
    args = parser.parse_args()

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

    # Interactive
    print()
    print("  eXT FRP Manager")
    print("  ---------------")
    print("  [1] Classic CLI  (recommended)")
    print("  [2] Textual TUI  (experimental)")
    print()
    try:
        choice = input("  Choose [1]: ").strip() or "1"
    except (EOFError, KeyboardInterrupt):
        choice = "1"

    if choice == "2":
        try:
            from .tui.app import run
            run()
        except Exception as e:
            print(f"TUI failed: {e}")
            print("Falling back to CLI...")
            from .cli import run as cli_run
            cli_run()
    else:
        from .cli import run as cli_run
        cli_run()


if __name__ == "__main__":
    main()
