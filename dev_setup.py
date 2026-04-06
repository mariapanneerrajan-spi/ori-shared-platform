#!/usr/bin/env python
"""
ORI Shared Platform — Dev Build Setup

Cross-platform build script for development mode.
Builds OpenRV packages (.rvpkg), installs them locally,
and installs Python dependencies into OpenRV's Python.

Usage:
    python dev_setup.py build          # Build + install rvpkgs
    python dev_setup.py install-deps   # Install Python deps into OpenRV Python
    python dev_setup.py all            # Both (default)
    python dev_setup.py clean          # Remove local_install/

Requires RV_HOME environment variable (or --rv-home flag)
pointing to your OpenRV installation directory.
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


def find_rvpkg(rv_home):
    if platform.system() == "Windows":
        candidates = [rv_home / "bin" / "rvpkg.exe", rv_home / "bin" / "rvpkg"]
    else:
        candidates = [rv_home / "bin" / "rvpkg"]
    for c in candidates:
        if c.is_file():
            return c
    print(f"ERROR: rvpkg not found in {rv_home / 'bin'}")
    print("Searched:", [str(c) for c in candidates])
    sys.exit(1)


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
    pkg_dir = ROOT_DIR / "rpa" / "open_rv" / "pkgs" / "rpa_core_pkg"
    api_dir = ROOT_DIR / "rpa" / "open_rv" / "rpa_core" / "api"
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
    pkg_dir = ROOT_DIR / "rpa" / "open_rv" / "pkgs" / "rpa_widgets_pkg"
    pkg_path = output_dir / "rpa_widgets-1.0.rvpkg"

    with zipfile.ZipFile(pkg_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(pkg_dir / "PACKAGE", "PACKAGE")
        zf.write(pkg_dir / "rpa_widgets_mode.py", "rpa_widgets_mode.py")

    print(f"  Built {pkg_path.name}")
    return pkg_path


def build_rvpkg_node_graph_editor(output_dir):
    """Build node_graph_editor-1.0.rvpkg from source files."""
    pkg_dir = ROOT_DIR / "rpa" / "open_rv" / "pkgs" / "node_graph_editor"
    pkg_path = output_dir / "node_graph_editor-1.0.rvpkg"

    with zipfile.ZipFile(pkg_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(pkg_dir / "PACKAGE", "PACKAGE")
        zf.write(pkg_dir / "node_graph_editor_mode.py", "node_graph_editor_mode.py")

    print(f"  Built {pkg_path.name}")
    return pkg_path


# ---------------------------------------------------------------------------
# Install rvpkg via rvpkg CLI
# ---------------------------------------------------------------------------

def run_rvpkg(rvpkg_exe, args, check=True):
    """Run an rvpkg command, optionally ignoring errors."""
    cmd = [str(rvpkg_exe)] + [str(a) for a in args]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"  FAILED: {' '.join(cmd)}")
        if result.stdout:
            print(f"    stdout: {result.stdout.strip()}")
        if result.stderr:
            print(f"    stderr: {result.stderr.strip()}")
        sys.exit(1)
    return result


def install_rvpkg(rvpkg_exe, support_path, pkg_file):
    """Install a single .rvpkg into the support path."""
    installed = support_path / "Packages" / pkg_file.name

    # Remove previous installation (ignore errors if not present)
    run_rvpkg(rvpkg_exe, ["-uninstall", installed], check=False)
    run_rvpkg(rvpkg_exe, ["-remove", installed], check=False)

    # Install fresh
    run_rvpkg(rvpkg_exe, ["-add", support_path, pkg_file])
    run_rvpkg(rvpkg_exe, ["-install", installed])
    run_rvpkg(rvpkg_exe, ["-optin", installed])

    print(f"  Installed {pkg_file.name}")


def install_node_graph_editor_python(support_path):
    """Copy node_graph_editor Python subpackage to support path."""
    src = ROOT_DIR / "rpa" / "open_rv" / "pkgs" / "node_graph_editor" / "node_graph_editor"
    dst = support_path / "Python" / "node_graph_editor"
    if dst.exists():
        shutil.rmtree(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dst)
    print("  Copied node_graph_editor Python package")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_build(rv_home):
    """Build and install all rvpkgs to local_install/."""
    rvpkg_exe = find_rvpkg(rv_home)
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
        build_rvpkg_node_graph_editor(build_dir),
    ]

    print("Installing rvpkg files...")
    for pkg in pkgs:
        install_rvpkg(rvpkg_exe, support_path, pkg)

    # Copy node_graph_editor Python subpackage
    install_node_graph_editor_python(support_path)

    # Clean temp build directory
    shutil.rmtree(build_dir)

    print(f"\nBuild complete. RV_SUPPORT_PATH: {support_path}")


def cmd_install_deps(rv_home):
    """Install Python dependencies into OpenRV's Python."""
    rv_python = find_rv_python(rv_home)

    req_files = [
        ROOT_DIR / "rpa" / "build_scripts" / "requirements.txt",
        ROOT_DIR / "itview" / "requirements.txt",
    ]

    print("Installing Python dependencies into OpenRV Python...")
    for req in req_files:
        if req.is_file():
            print(f"  Installing from {req.relative_to(ROOT_DIR)}...")
            result = subprocess.run(
                [str(rv_python), "-m", "pip", "install", "-r", str(req)],
                capture_output=True,
                text=True,
            )
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

    rv_home = find_rv_home(args.rv_home)
    print(f"Using RV_HOME: {rv_home}")

    if args.command in ("build", "all"):
        cmd_build(rv_home)

    if args.command in ("install-deps", "all"):
        cmd_install_deps(rv_home)

    print("\nDev setup complete!")


if __name__ == "__main__":
    main()
