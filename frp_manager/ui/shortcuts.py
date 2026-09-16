"""Keyboard shortcuts — reads raw bytes via os.read on stdin fd.

This is the most reliable approach because it bypasses Python's
buffered I/O layer that can break raw terminal reads.
"""
from __future__ import annotations

import os
import sys
import select
from typing import Optional


FKEY_SEQUENCES = {
    "\x1bOP": "F1",
    "\x1bOQ": "F2",
    "\x1bOR": "F3",
    "\x1bOS": "F4",
    "\x1b[11~": "F1",
    "\x1b[12~": "F2",
    "\x1b[13~": "F3",
    "\x1b[14~": "F4",
    "\x1b[15~": "F5",
    "\x1b[17~": "F6",
    "\x1b[18~": "F7",
    "\x1b[19~": "F8",
    "\x1b[20~": "F9",
    "\x1b[21~": "F10",
    "\x1b[23~": "F11",
    "\x1b[24~": "F12",
    "\x1b[[A": "F1",
    "\x1b[[B": "F2",
    "\x1b[[C": "F3",
    "\x1b[[D": "F4",
    "\x1b[[E": "F5",
    # Arrows
    "\x1b[A": "UP",
    "\x1b[B": "DOWN",
    "\x1b[C": "RIGHT",
    "\x1b[D": "LEFT",
    "\x1b[H": "HOME",
    "\x1b[F": "END",
    "\x1b[2~": "INSERT",
    "\x1b[3~": "DELETE",
    "\x1b[5~": "PGUP",
    "\x1b[6~": "PGDN",
}


def _read_byte(fd: int, timeout: float) -> Optional[bytes]:
    """Read a single byte from fd with timeout. Returns None if timeout."""
    try:
        r, _, _ = select.select([fd], [], [], timeout)
        if not r:
            return None
        data = os.read(fd, 1)
        return data if data else None
    except (BlockingIOError, OSError):
        return None


def _read_sequence(fd: int, first_byte: bytes,
                    settle: float = 0.05) -> bytes:
    """Read rest of an escape sequence after receiving ESC.

    Args:
        fd: file descriptor
        first_byte: the initial ESC byte
        settle: seconds to wait between attempts

    Returns:
        Complete byte sequence.
    """
    seq = bytearray(first_byte)
    # Read up to 8 more bytes; stop when nothing more arrives
    for _ in range(8):
        b = _read_byte(fd, settle)
        if b is None:
            break
        seq.extend(b)
        # Early exit if we hit a known sequence
        try:
            s = seq.decode("ascii", errors="replace")
            if s in FKEY_SEQUENCES:
                break
        except Exception:
            pass
    return bytes(seq)


def _normalize(data: bytes) -> str:
    """Convert raw bytes to a key name."""
    if not data:
        return ""

    try:
        s = data.decode("utf-8", errors="replace")
    except Exception:
        return ""

    if s in FKEY_SEQUENCES:
        return FKEY_SEQUENCES[s]

    # Single-byte cases
    if len(s) == 1:
        c = s
        if c in ("\r", "\n"):
            return "ENTER"
        if c == "\x1b":
            return "ESC"
        if c in ("\x7f", "\x08"):
            return "BACKSPACE"
        if c == "\t":
            return "TAB"
        if c == "\x03":
            raise KeyboardInterrupt
        if c == "\x04":  # Ctrl+D
            raise EOFError

    return s


def read_key_blocking() -> str:
    """Block until one key is pressed. Reads F-keys atomically."""
    try:
        import termios
        import tty
    except ImportError:
        try:
            return input().strip()
        except (EOFError, KeyboardInterrupt):
            return ""

    if not sys.stdin.isatty():
        try:
            return input().strip()
        except (EOFError, KeyboardInterrupt):
            return ""

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)

        # Blocking read of first byte
        first = None
        while first is None:
            try:
                r, _, _ = select.select([fd], [], [], None)
                if r:
                    first = os.read(fd, 1)
            except (OSError, KeyboardInterrupt):
                raise

        if not first:
            return ""

        # If first byte is ESC, try to read rest of sequence
        if first == b"\x1b":
            full = _read_sequence(fd, first)
            return _normalize(full)

        return _normalize(first)

    except KeyboardInterrupt:
        raise
    except Exception:
        return ""
    finally:
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except Exception:
            pass


def read_key_with_timeout(timeout: float = 0.5) -> Optional[str]:
    """Non-blocking version with timeout. Returns None if no key."""
    try:
        import termios
        import tty
    except ImportError:
        return None

    if not sys.stdin.isatty():
        return None

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)

        # Wait for first byte
        r, _, _ = select.select([fd], [], [], timeout)
        if not r:
            return None

        first = os.read(fd, 1)
        if not first:
            return None

        if first == b"\x1b":
            full = _read_sequence(fd, first)
            return _normalize(full)

        return _normalize(first)

    except KeyboardInterrupt:
        raise
    except Exception:
        return None
    finally:
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except Exception:
            pass


def supports_raw_mode() -> bool:
    try:
        import termios  # noqa
        import tty  # noqa
        return sys.stdin.isatty()
    except ImportError:
        return False


def read_key_or_prompt(prompt_text: str = "") -> str:
    if supports_raw_mode():
        if prompt_text:
            sys.stdout.write(prompt_text)
            sys.stdout.flush()
        return read_key_blocking() or ""
    try:
        return input(prompt_text or "").strip()
    except (EOFError, KeyboardInterrupt):
        return ""
