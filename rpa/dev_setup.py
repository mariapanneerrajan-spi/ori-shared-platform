#!/usr/bin/env python
"""
ORI Shared Platform — Dev Build Setup

Cross-platform build script for development mode.
Builds OpenRV packages (.rvpkg), installs them locally,
and installs Python dependencies into OpenRV's Python.

Usage (run from the repo root):
    python rpa/dev_setup.py build          # Build + install rvpkgs (no RV_HOME needed)
    python rpa/dev_setup.py install-deps   # Install Python deps into OpenRV Python
    python rpa/dev_setup.py all            # Both (default)
    python rpa/dev_setup.py clean          # Remove rpa/local_install/

RV_HOME environment variable (or --rv-home flag) is required for
install-deps and all commands (not needed for build-only).
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent


# ---------------------------------------------------------------------------
# Environment discovery
# ---------------------------------------------------------------------------

def find_rv_home(override=None):
    rv_home = override or os.environ.get("RV_HOME")
    if not rv_home:
        print("ERROR: RV_HOME is not set.")
        print("Set it to your OpenRV installation directory:")
        print("  export RV_HOME=/path/to/OpenRV        (Linux/Mac)")
        print("  set RV_HOME=C:\\path\\to\\OpenRV         (Windows)")
        sys.exit(1)
    rv_home = Path(rv_home)
    if not rv_home.is_dir():
        print(f"ERROR: RV_HOME={rv_home} is not a valid directory.")
        sys.exit(1)
    return rv_home



def find_rv_python(rv_home):
    if platform.system() == "Windows":
        candidates = [
            rv_home / "bin" / "python3.exe",
            rv_home / "bin" / "python.exe",
        ]
    else:
        candidates = [
            rv_home / "bin" / "python3",
            rv_home / "bin" / "python",
        ]
    for c in candidates:
        if c.is_file():
            return c
    print(f"ERROR: Python interpreter not found in {rv_home / 'bin'}")
    print("Searched:", [str(c) for c in candidates])
    sys.exit(1)


# ---------------------------------------------------------------------------
# Build rvpkg files
# ---------------------------------------------------------------------------

def build_rvpkg_rpa_core(output_dir):
    """Build rpa_core-1.0.rvpkg from source files."""
    pkg_dir = ROOT_DIR / "open_rv" / "pkgs" / "rpa_core_pkg"
    api_dir = ROOT_DIR / "open_rv" / "rpa_core" / "api"
    pkg_path = output_dir / "rpa_core-1.0.rvpkg"

    with zipfile.ZipFile(pkg_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(pkg_dir / "PACKAGE", "PACKAGE")
        zf.write(pkg_dir / "rpa_core_mode.py", "rpa_core_mode.py")
        for ext in ("*.mu", "*.glsl", "*.gto"):
            for f in api_dir.glob(ext):
                zf.write(f, f.name)

    print(f"  Built {pkg_path.name}")
    return pkg_path


def build_rvpkg_rpa_widgets(output_dir):
    """Build rpa_widgets-1.0.rvpkg from source files."""
    pkg_dir = ROOT_DIR / "open_rv" / "pkgs" / "rpa_widgets_pkg"
    pkg_path = output_dir / "rpa_widgets-1.0.rvpkg"

    with zipfile.ZipFile(pkg_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(pkg_dir / "PACKAGE", "PACKAGE")
        zf.write(pkg_dir / "rpa_widgets_mode.py", "rpa_widgets_mode.py")

    print(f"  Built {pkg_path.name}")
    return pkg_path


# ---------------------------------------------------------------------------
# Install rvpkg files and generate rvload2
# ---------------------------------------------------------------------------

def parse_package_manifest(pkg_path):
    """Parse a PACKAGE manifest from inside an .rvpkg zip.

    Returns a dict with keys: rv, openrv, optional, modes.
    Each mode has: file, menu, shortcut, event, load.
    """
    with zipfile.ZipFile(pkg_path, "r") as zf:
        text = zf.read("PACKAGE").decode("utf-8")

    pkg = {"rv": "", "openrv": "", "optional": False, "modes": []}
    current_mode = None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Top-level keys
        if line and not line[0].isspace() and ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip("'\"")
            if key == "rv":
                pkg["rv"] = val
            elif key == "openrv":
                pkg["openrv"] = val
            elif key == "optional":
                pkg["optional"] = val.lower() == "true"
            elif key == "modes":
                pass  # modes list follows
            continue

        # Mode entries (indented under modes:)
        if stripped.startswith("- file:"):
            current_mode = {
                "file": stripped.split(":", 1)[1].strip().strip("'\""),
                "menu": "",
                "shortcut": "",
                "event": "",
                "load": "immediate",
            }
            pkg["modes"].append(current_mode)
        elif current_mode and ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip().strip("'\"")
            if key in current_mode:
                current_mode[key] = val

    return pkg


def generate_rvload2(support_path, pkg_files):
    """Generate the Mu/rvload2 file so packages auto-load in OpenRV.

    The rvload2 format (version 4) is a CSV file:
      Line 1: version number (4)
      Subsequent lines: name,package,menu,shortcut,event,loaded,active,rvversion,optional,openrvversion
    """
    mu_dir = support_path / "Mu"
    mu_dir.mkdir(parents=True, exist_ok=True)

    entries = []
    for pkg_file in pkg_files:
        manifest = parse_package_manifest(pkg_file)
        for mode in manifest["modes"]:
            # Strip .py/.mu extension to get mode name
            name = mode["file"]
            if name.endswith(".py") or name.endswith(".mu"):
                name = name[:-3]

            is_immediate = mode["load"] == "immediate"
            menu = mode["menu"] if mode["menu"] else "nil"
            shortcut = mode["shortcut"] if mode["shortcut"] else "nil"
            event = mode["event"] if mode["event"] else "nil"

            entry = (
                f"{name},"
                f"{pkg_file.name},"
                f"{menu},"
                f"{shortcut},"
                f"{event},"
                f"{'true' if is_immediate else 'false'},"
                f"{'true' if is_immediate else 'false'},"
                f"{manifest['rv']},"
                f"{'true' if manifest['optional'] else 'false'},"
                f"{manifest['openrv']}"
            )
            entries.append(entry)

    rvload2_path = mu_dir / "rvload2"
    rvload2_path.write_text("4\n" + "\n".join(entries) + "\n", encoding="utf-8")
    print(f"  Generated rvload2 with {len(entries)} mode(s)")


def install_rvpkg(support_path, pkg_file):
    """Install a .rvpkg: copy the zip and extract contents to the right dirs.

    Mirrors what OpenRV's rvpkg -install does:
      .py  → Python/
      .mu  → Mu/
      .glsl/.gto → Nodes/
      PACKAGE → skipped (stays in the zip)
    """
    # Copy the rvpkg zip into Packages/
    dest = support_path / "Packages" / pkg_file.name
    shutil.copy2(pkg_file, dest)

    # Extract contents to appropriate directories
    with zipfile.ZipFile(pkg_file, "r") as zf:
        for member in zf.namelist():
            if member == "PACKAGE":
                continue

            basename = Path(member).name
            if member.endswith(".py"):
                out_dir = support_path / "Python"
            elif member.endswith((".mu", ".mud", ".muc")):
                out_dir = support_path / "Mu"
            elif member.endswith((".glsl", ".gto")):
                out_dir = support_path / "Nodes"
            else:
                pkg_name = pkg_file.stem.rsplit("-", 1)[0]  # e.g. rpa_core
                out_dir = support_path / "SupportFiles" / pkg_name

            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / basename
            out_path.write_bytes(zf.read(member))

    print(f"  Installed {pkg_file.name}")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_build():
    """Build and install all rvpkgs to local_install/."""
    local_install = ROOT_DIR / "local_install"
    support_path = local_install / "lib" / "open_rv"

    # Clean entire local_install and recreate
    print("Cleaning local_install directory...")
    if local_install.exists():
        shutil.rmtree(local_install)
    (support_path / "Packages").mkdir(parents=True)

    # Build rvpkg files into a temp directory
    build_dir = ROOT_DIR / "local_install" / "_build_tmp"
    build_dir.mkdir(parents=True, exist_ok=True)

    print("Building rvpkg files...")
    pkgs = [
        build_rvpkg_rpa_core(build_dir),
        build_rvpkg_rpa_widgets(build_dir),
    ]

    print("Installing rvpkg files...")
    for pkg in pkgs:
        install_rvpkg(support_path, pkg)

    # Generate rvload2 so packages auto-load in OpenRV
    generate_rvload2(support_path, [support_path / "Packages" / p.name for p in pkgs])

    # Clean temp build directory
    shutil.rmtree(build_dir)

    print(f"\nBuild complete. RV_SUPPORT_PATH: {support_path}")


def _snapshot_rv_packages(rv_python):
    """Capture OpenRV's existing packages as a pip constraints file.

    Returns the path to a temporary constraints file that pins every
    pre-installed package to its current version, preventing pip from
    upgrading (or downgrading) any of them.
    """
    constraints_path = ROOT_DIR / "local_install" / "_rv_constraints.txt"
    constraints_path.parent.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [str(rv_python), "-m", "pip", "freeze"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("  WARNING: Could not snapshot OpenRV packages (pip freeze failed)")
        return None

    constraints_path.write_text(result.stdout, encoding="utf-8")
    return constraints_path


def cmd_install_deps(rv_home):
    """Install Python dependencies into OpenRV's Python."""
    rv_python = find_rv_python(rv_home)

    # Snapshot existing OpenRV packages so pip never upgrades them
    print("Snapshotting OpenRV's existing packages as constraints...")
    constraints_file = _snapshot_rv_packages(rv_python)
    if constraints_file:
        print(f"  Constraints file: {constraints_file}")
    else:
        print("  WARNING: Proceeding without constraints — existing packages may be upgraded!")

    req_files = [
        ROOT_DIR / "requirements.txt",
    ]

    print("Installing Python dependencies into OpenRV Python...")
    for req in req_files:
        if req.is_file():
            print(f"  Installing from {req.relative_to(ROOT_DIR)}...")
            cmd = [str(rv_python), "-m", "pip", "install", "-r", str(req)]
            if constraints_file:
                cmd += ["-c", str(constraints_file)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"  WARNING: pip install failed for {req.name}")
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(result.stderr)
            else:
                print(f"  Done ({req.name})")
        else:
            print(f"  Skipping {req.relative_to(ROOT_DIR)} (not found)")

    # Install Playwright browser binaries
    print("  Installing Playwright Chromium browser...")
    result = subprocess.run(
        [str(rv_python), "-m", "playwright", "install", "chromium"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("  WARNING: Playwright browser install failed")
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
    else:
        print("  Done (playwright chromium)")

    print("\nDependency installation complete.")


def cmd_clean():
    """Remove the local_install directory."""
    local_install = ROOT_DIR / "local_install"
    if local_install.exists():
        shutil.rmtree(local_install)
        print("Removed local_install/")
    else:
        print("Nothing to clean (local_install/ does not exist)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="ORI Shared Platform — Dev Build Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="all",
        choices=["build", "install-deps", "all", "clean"],
        help="Command to run (default: all)",
    )
    parser.add_argument(
        "--rv-home",
        help="Path to OpenRV installation (overrides RV_HOME env var)",
    )
    args = parser.parse_args()

    if args.command == "clean":
        cmd_clean()
        return

    if args.command in ("build", "all"):
        cmd_build()

    if args.command in ("install-deps", "all"):
        rv_home = find_rv_home(args.rv_home)
        print(f"Using RV_HOME: {rv_home}")
        cmd_install_deps(rv_home)

    print("\nDev setup complete!")


if __name__ == "__main__":
    main()
