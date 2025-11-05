#!/usr/bin/env python3
"""
xr_loopback_set.py

Create (ensure) Cisco IOS-XR Loopback interfaces and set their descriptions.
Generate a rollback that truly reverts state.

Features:
- Single or CSV bulk mode
- Dry-run preview (no device changes)
- Backup + before/after diff
- Optional 'commit confirmed <seconds>' safety
- Robust rollback generation based on per-interface probes

Usage examples:

# Single loopback
  python xr_loopback_set.py 100 --description "Mgmt Loopback"

# CSV bulk
  python xr_loopback_set.py --csv loopbacks.csv

# Dry-run
  python xr_loopback_set.py 300 --description "Anycast VIP" --dry-run

# Generate rollback commands (before applying)
  python xr_loopback_set.py --csv loopbacks.csv --generate-rollback rollback.cmds

# Apply rollback commands
  python xr_loopback_set.py --apply-rollback rollback.cmds

# Prefer deleting 'empty' loopbacks (only description) on rollback (default: True)
  python xr_loopback_set.py --csv loopbacks.csv --generate-rollback rollback.cmds --delete-empty-loopbacks
"""

import os
import sys
import csv
import difflib
import argparse
import datetime
from typing import List, Tuple, Dict, Optional

from dotenv import load_dotenv
from netmiko import ConnectHandler


# ==============================================================================
# Helpers
# ==============================================================================

def normalize_loopback(name_or_id: str) -> str:
    """Normalize a loopback name or numeric ID to 'LoopbackN'."""
    n = name_or_id.strip()
    if n.lower().startswith("loopback"):
        suffix = n[len("loopback"):]
        if not suffix.isdigit():
            raise ValueError(f"Invalid Loopback interface: {name_or_id}")
        return f"Loopback{int(suffix)}"
    if not n.isdigit():
        raise ValueError(f"Loopback must be an integer or 'LoopbackN': {name_or_id}")
    return f"Loopback{int(n)}"


def load_device_from_env(args) -> dict:
    """Load device credentials from env or CLI overrides."""
    load_dotenv()
    host = args.host or os.getenv("XR_HOST")
    user = args.user or os.getenv("XR_USER")
    pwd  = args.password or os.getenv("XR_PASS")

    missing = [k for k, v in [("XR_HOST", host), ("XR_USER", user), ("XR_PASS", pwd)] if not v]
    if missing and not args.apply_rollback:
        raise SystemExit(f"Missing credentials/env: {', '.join(missing)}. Use env or --host/--user/--password.")

    return {
        "device_type": "cisco_xr",
        "host": host,
        "username": user,
        "password": pwd,
        "fast_cli": True,
    }


def parse_csv_pairs(csv_path: str) -> List[Tuple[str, str]]:
    """Read CSV with columns: loopback,description."""
    pairs: List[Tuple[str, str]] = []
    with open(csv_path, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            lb = normalize_loopback(row["loopback"])
            desc = (row["description"] or "").strip()
            if not desc:
                raise ValueError(f"Missing description for {lb} in CSV.")
            pairs.append((lb, desc))
    if not pairs:
        raise ValueError("CSV contained no rows.")
    return pairs


def build_commands_bulk(pairs: List[Tuple[str, str]]) -> List[str]:
    """Build CLI commands to ensure each loopback and set its description."""
    cmds: List[str] = []
    for lb, desc in pairs:
        cmds += [f"interface {lb}", f"description {desc}"]
    return cmds


def read_running(conn) -> str:
    """Grab full running-config."""
    return conn.send_command("show running-config")


def backup_running(running: str, host: str) -> str:
    """Save a timestamped backup of the running-config."""
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    os.makedirs("backups", exist_ok=True)
    path = os.path.join("backups", f"{host}-{ts}.running-config.txt")
    with open(path, "w") as f:
        f.write(running)
    return path


# ==============================================================================
# Per-interface probes (robust existence + “emptiness” detection)
# ==============================================================================

def get_interface_state(conn, loopback: str) -> Dict[str, Optional[str]]:
    """Probe a specific Loopback's running-config stanza.

    Returns a dict:
      {
        'exists': bool,                   # whether a stanza is present
        'description': Optional[str],     # previous description (if any)
        'lines': List[str],               # raw lines under the stanza (excl. 'interface ...')
      }
    """
    text = conn.send_command(f"show running-config interface {loopback}")
    lines = [ln.rstrip() for ln in text.splitlines() if ln.strip()]

    exists = False
    description: Optional[str] = None
    sub_lines: List[str] = []

    if lines and lines[0].startswith("interface "):
        exists = True
        # everything after first line belongs to the stanza
        for ln in lines[1:]:
            # XR outputs sub-commands indented; keep raw but trim leading spaces for analysis
            raw = ln.lstrip()
            sub_lines.append(raw)
            if raw.startswith("description "):
                description = raw[len("description "):].strip()

    return {"exists": exists, "description": description, "lines": sub_lines}


def is_empty_loopback(sub_lines: List[str]) -> bool:
    """Heuristic: an 'empty' loopback has NO sub-commands other than an optional description."""
    if not sub_lines:
        return True
    # Allow only 'description ...' lines; anything else means 'has real config'
    for ln in sub_lines:
        if not ln or ln.startswith("description "):
            continue
        return False
    return True


# ==============================================================================
# Rollback generation (correct deletion behavior)
# ==============================================================================

def generate_rollback_for_pairs(
    before_states: Dict[str, Dict[str, Optional[str]]],
    target_pairs: List[Tuple[str, str]],
    delete_empty_loopbacks: bool = True,
) -> List[str]:
    """Create rollback commands that truly revert device state.

    - If a loopback did NOT exist before -> delete it:   'no interface LoopbackN'
    - If it existed and stanza was 'empty' (only description) and delete_empty_loopbacks=True -> delete it
    - Otherwise -> restore previous description (or clear with 'no description')
    """
    cmds: List[str] = []

    for lb, _new_desc in target_pairs:
        st = before_states[lb]  # must be present
        exists = bool(st["exists"])
        desc  = st["description"]
        lines = st["lines"] or []

        if not exists:
            cmds.append(f"no interface {lb}")
            continue

        if delete_empty_loopbacks and is_empty_loopback(lines):
            cmds.append(f"no interface {lb}")
            continue

        # Restore description on pre-existing, non-empty interface
        cmds.append(f"interface {lb}")
        if desc:
            cmds.append(f"description {desc}")
        else:
            cmds.append("no description")

    return cmds


# ==============================================================================
# Apply + Commit
# ==============================================================================

def apply_and_commit(conn, cmds: List[str], commit_confirmed: int = 0) -> None:
    """Apply configuration commands and commit on IOS-XR."""
    resp = conn.send_config_set(cmds)
    print("\n=== device response ===\n", resp)
    if commit_confirmed and commit_confirmed > 0:
        print(f"\n=== commit confirmed {commit_confirmed} ===")
        print(conn.send_command(f"commit confirmed {commit_confirmed}"))
        print("\nFinalizing commit after validation...")
        print(conn.send_command("commit"))
    else:
        print("\n=== commit ===")
        print(conn.send_command("commit"))


def show_diff(before: str, after: str) -> None:
    """Print a unified diff between two running-config snapshots."""
    diff = list(difflib.unified_diff(
        before.splitlines(), after.splitlines(),
        fromfile="before", tofile="after", lineterm=""
    ))
    print("\n=== running-config diff (before → after) ===")
    if diff:
        print("\n".join(diff[:1200]))
        if len(diff) > 1200:
            print("\n...diff truncated...")
    else:
        print("(no changes detected)")


# ==============================================================================
# CLI
# ==============================================================================

def get_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Ensure IOS-XR Loopback(s) exist and set descriptions.")
    p.add_argument("loopback", nargs="?", help="Loopback ID or name (e.g., 100 or Loopback100).")
    p.add_argument("--description", help="Description for single loopback mode.")
    p.add_argument("--csv", help="CSV file (loopback,description) for bulk mode.")
    p.add_argument("--dry-run", action="store_true", help="Preview commands, no commit.")
    p.add_argument("--commit-confirmed", type=int, default=0, metavar="SECONDS",
                   help="Use 'commit confirmed SECONDS' safety mode.")
    p.add_argument("--generate-rollback", metavar="FILE",
                   help="Generate rollback command file based on current per-interface state.")
    p.add_argument("--apply-rollback", metavar="FILE",
                   help="Apply commands from a rollback file and commit.")
    p.add_argument("--delete-empty-loopbacks", action="store_true", default=True,
                   help="On rollback, delete loopbacks whose only sub-command was a description (default: enabled).")
    p.add_argument("--keep-empty-loopbacks", action="store_true",
                   help="Override: do NOT delete 'empty' loopbacks; just clear their description.")

    # Connection
    p.add_argument("--host", help="Override XR_HOST env var.")
    p.add_argument("--user", help="Override XR_USER env var.")
    p.add_argument("--password", help="Override XR_PASS env var.")
    return p.parse_args()


# ==============================================================================
# Main
# ==============================================================================

def main() -> None:
    args = get_args()

    # Flag resolution for empty-loopback deletion behavior
    delete_empty = args.delete_empty_loopbacks and not args.keep_empty_loopbacks

    # Apply rollback file and exit
    if args.apply_rollback:
        device = load_device_from_env(args)
        cmds = _read_commands_from_file(args.apply_rollback)
        print("Loaded rollback commands:")
        for c in cmds:
            print("  ", c)
        if args.dry_run:
            print("\n--dry-run: would apply rollback (no commit).")
            return
        with ConnectHandler(**device) as conn:
            before = read_running(conn)
            backup = backup_running(before, device["host"])
            print(f"\nBackup saved: {backup}")
            apply_and_commit(conn, cmds, commit_confirmed=args.commit_confirmed)
            after = read_running(conn)
        show_diff(before, after)
        return

    # Build targets: single or CSV
    if args.csv:
        target_pairs = parse_csv_pairs(args.csv)
    else:
        if not args.loopback or not args.description:
            raise SystemExit("Provide LOOPBACK + --description, or use --csv for bulk mode.")
        target_pairs = [(normalize_loopback(args.loopback), args.description)]

    planned_cmds = build_commands_bulk(target_pairs)
    print("Planned commands:")
    for c in planned_cmds:
        print("  ", c)

    if args.dry_run and not args.generate_rollback:
        print("\n--dry-run: preview only; no changes made.")
        return

    device = load_device_from_env(args)

    with ConnectHandler(**device) as conn:
        # Backup before any changes
        before_full = read_running(conn)
        backup = backup_running(before_full, device["host"])
        print(f"\nBackup saved: {backup}")

        # === Robust rollback generation (per-interface probes) ===
        if args.generate_rollback:
            before_states: Dict[str, Dict[str, Optional[str]]] = {}
            for lb, _desc in target_pairs:
                before_states[lb] = get_interface_state(conn, lb)

            rb_cmds = generate_rollback_for_pairs(
                before_states, target_pairs, delete_empty_loopbacks=delete_empty
            )
            _save_commands_to_file(rb_cmds, args.generate_rollback)
            print(f"Rollback file generated: {args.generate_rollback}")
            for c in rb_cmds:
                print("  ", c)

            if args.dry_run:
                print("\n--dry-run: rollback generated only.")
                return

        # === Apply intended changes and commit ===
        apply_and_commit(conn, planned_cmds, commit_confirmed=args.commit_confirmed)

        # Post-change diff for visibility
        after_full = read_running(conn)

    show_diff(before_full, after_full)


# ==============================================================================
# File I/O for rollback commands
# ==============================================================================

def _save_commands_to_file(cmds: List[str], path: str) -> None:
    with open(path, "w") as f:
        f.write("\n".join(cmds) + "\n")


def _read_commands_from_file(path: str) -> List[str]:
    with open(path) as f:
        return [ln.rstrip("\n") for ln in f if ln.strip()]


# ==============================================================================
# Entrypoint
# ==============================================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        sys.exit(1)
