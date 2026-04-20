The App
=======

.. contents::
   :local:
   :depth: 1

==========
Overview
==========

The App is a review product built on top of RPA. It owns the user-visible
UI, loads RPA-based plugins, and uses OpenRV as its underlying review
playback system — but users never see OpenRV's own UI.

The host window is ``AppMainWindow`` (``rpa/app/app_main_window.py``). On
startup:

1. OpenRV's stock main window is **hidden** (not destroyed — OpenRV's
   ``GLView`` holds a raw pointer to ``RvDocument``, so the stock window
   must stay alive for the viewport to render).
2. OpenRV's viewport widget is re-parented into ``AppMainWindow`` as the
   central widget.
3. ``AppMainWindow`` provides its own menu bar (``App``, ``Session``,
   ``Plugins``, plus whatever menus plugins register via
   ``get_menu(name)``), dark title bar on Windows, fullscreen toggle, and
   window-layout persistence via ``QSettings``.
4. The plugin manager is handed ``AppMainWindow`` and a freshly-built
   ``Rpa`` instance, and loads every plugin listed in the active plugin
   config.

The App is deliberately agnostic to which review system provided its
viewport. Any review-system-specific shutdown (e.g. closing OpenRV's
``RvDocument``) is performed by the review-system glue in response to
``AppMainWindow.SIG_CLOSED`` — not by the App itself.

================
Plugin Manager
================

The plugin manager (``rpa/app/plugin_manager/``) is the App's primary
extensibility mechanism. It:

* Reads the active plugin config (``rpa/plugins/open_app_plugins.cfg`` by
  default, resolved from ``RPA_APP_CORE_PLUGINS_CONFIG``) and turns each
  line into a plugin folder path.
* Registers each plugin folder as a top-level importable module via
  ``ImportPathEnforcer``, so a plugin's sibling files import as
  ``<plugin_folder>.<submodule>``. Plugins are **not** Python sub-packages
  of ``rpa.plugins`` — do not add ``__init__.py`` to ``rpa/plugins/``.
* Loads each plugin's metadata (``<plugin>/<plugin>.json``), imports
  ``<plugin>/<plugin>.py``, instantiates the class named in the metadata,
  and calls the plugin's ``app_init(self, app)``.
* After every plugin is initialized, calls each plugin's optional
  ``post_app_init(self)`` hook so plugins can do work that depends on
  other plugins already being up.

CLI args declared by plugins (via an optional ``cli_args.py``) are parsed
by the launcher *before* OpenRV boots, stashed in an env var, and
rehydrated into an ``argparse.Namespace`` that plugins read from
``app.cmd_line_args``.

====================
Writing a plugin
====================

A plugin is just a folder under ``rpa/plugins/``. Minimum contents:

* ``<plugin_name>/<plugin_name>.py`` — entry-point module containing the
  plugin class.
* ``<plugin_name>/<plugin_name>.json`` — metadata file with these keys:
  ``class_name``, ``plugin_name``, ``description``, ``author_email``,
  ``app_version``.

Optional:

* ``<plugin_name>/cli_args.py`` — contributes argparse args that are
  parsed before OpenRV starts.
* ``<plugin_name>/widget/`` — PySide widgets owned by this plugin and the
  resources they use.

Entry-point shape:

.. code-block:: python

   class MyPlugin:

       def app_init(self, app):
           # app exposes: rpa, dbid_mapper, main_window, cmd_line_args,
           # viewport_user_input, settings_api
           self._rpa = app.rpa
           self._widget = MyWidget(self._rpa, app.main_window)
           # parent widgets to app.main_window; use app.main_window.get_menu(...)
           # to add menu actions.

       def post_app_init(self):
           # Optional: runs after every plugin's app_init has finished.
           pass

       def register_settings(self, register):
           # Optional: declare user-visible settings via the settings API.
           pass

All review operations must go through ``app.rpa`` — plugins never talk to
OpenRV (or any underlying review system) directly.

==================
Shared widgets
==================

Widgets reused by more than one plugin live under
``rpa/plugins/rpa_widgets/`` and are imported as
``rpa_widgets.<subpackage>.<module>``:

* ``rpa_widgets/sub_widgets/`` — small shared primitives (color_circle,
  slider_toolbar, striped_frame, title_media_editor, …).
* ``rpa_widgets/session_io/`` — OTIO session reader/writer, used by
  ``app_session_io`` and ``session_auto_saver``.
* ``rpa_widgets/rpa_interpreter/`` — used by the ``rpa_interpreter`` and
  ``clips_loop_mode_toggler`` plugins.
* ``rpa_widgets/test_widgets/`` — manual-test harnesses for the RPA APIs
  (not loaded as plugins).

``rpa_widgets`` is **not** a plugin and is intentionally absent from the
plugin config.

.. code-block:: python

   from rpa_widgets.sub_widgets.slider_toolbar import SliderToolBar
   from rpa_widgets.session_io.session_io import SessionIO

==================
Bundled plugins
==================

The default plugin set (``rpa/plugins/open_app_plugins.cfg``), grouped by
role:

* **App-level** — ``hotkey_editor``, ``session_auto_saver``.
* **Session I/O** — ``app_session_io``.
* **Session management** — ``app_session_manager``,
  ``app_session_assistant``.
* **Timeline / playback** — ``anim_edit``, ``timeline``,
  ``clips_loop_mode_toggler``.
* **Viewport / view** — ``background_modes``, ``interactive_modes``,
  ``transforms``, ``viewport_appearance``, ``viewport_user_input_manager``,
  ``view_controller``, ``mask``.
* **Color** — ``image_controller``, ``color``, ``app_color_corrector``.
* **Review** — ``annotation``.
* **Help / introspection** — ``rpa_app_info_hub``, ``rpa_interpreter``,
  ``session_tree_viewer``, ``help_menu``, ``app_console_logger``.

Each plugin folder contains its own ``widget/`` subfolder (when it owns
UI) — consult the folder for the plugin's specific behavior.

=================
Settings widget
=================

The plugin manager ships a settings infrastructure
(``rpa/app/plugin_manager/settings_widget/``) that provides typed editors
(boolean, color, enum, number, path, string, array). Plugins opt in by
implementing ``register_settings(register)``; the App exposes a dockable
Settings panel on ``Ctrl+,`` and persists values alongside the App's
other ``QSettings`` state.
