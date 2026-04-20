Build and Launch
================

.. contents::
   :local:
   :depth: 1

=============
Prerequisites
=============

- OpenRV installed locally. Set the ``RV_HOME`` environment variable to the
  OpenRV install root.
- Python 3 available on ``PATH``.

=====================
Build the RV Packages
=====================

From the repo root:

.. code-block:: shell

   python rpa/dev_setup.py build

This produces ``rpa_core-1.0.rvpkg`` and ``rpa_widgets-1.0.rvpkg`` under
``rpa/local_install/lib/open_rv/`` and generates the Mu ``rvload2`` manifest
so OpenRV auto-loads the packages. No ``RV_HOME`` required for this step.

========================================
Install Python deps into OpenRV's Python
========================================

.. code-block:: shell

   python rpa/dev_setup.py install-deps

Reads ``rpa/requirements.txt`` (playwright, scipy, imageio) and ``pip
install``\ s them into OpenRV's bundled Python. The script first snapshots
OpenRV's existing packages as a pip constraints file so nothing already
shipped with OpenRV gets upgraded or downgraded. Requires ``RV_HOME``.

Other commands:

- ``python rpa/dev_setup.py all`` — runs ``build`` + ``install-deps`` in
  sequence (default when no subcommand is given).
- ``python rpa/dev_setup.py clean`` — removes ``rpa/local_install/``.

==========
Launch App
==========

.. code-block:: shell

   # Linux / macOS
   ./rpa/launch_app

   # Windows
   rpa\launch_app.bat

The launchers:

- set ``PYTHONPATH`` to the parent of ``rpa/`` so ``import rpa.*`` resolves
  from source,
- set ``RV_SUPPORT_PATH`` to ``rpa/local_install/lib/open_rv`` so OpenRV
  picks up the rvpkgs built above,
- set ``RPA_APP_CORE_PLUGINS_CONFIG`` to
  ``rpa/plugins/open_app_plugins.cfg``,
- ``cd`` to the parent of ``rpa/`` before executing Python so the ``rpa``
  **package directory** wins over the sibling ``rpa.py`` **module file** on
  Python's cwd-first ``sys.path``,
- ``exec`` ``python -m rpa.app.launch_app`` which parses plugin CLI args
  (from each plugin's optional ``cli_args.py``) *before* ``rv.exe`` boots,
  stashes them in an env var, and then ``execv``\ s ``rv.exe``.

Both launchers require ``RV_HOME``.

================================
Where logs and settings are kept
================================

- **Logs**: ``~/.rpa_app/rpa_app.log`` on Linux/macOS;
  ``%APPDATA%\rpa_app\rpa_app.log`` on Windows. Rotating file handler at
  10 MB / 5 backups.
- **Settings**: ``QSettings("imageworks.com", "rpa_app")``; the on-disk
  location depends on the OS (Qt decides).
