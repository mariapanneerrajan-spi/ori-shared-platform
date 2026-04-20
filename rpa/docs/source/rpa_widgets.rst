RPA Widgets
===========

.. contents::
   :local:
   :depth: 1

==========================
Where are the RPA widgets?
==========================

There is no longer a separate ``rpa/widgets/`` tree. UI code now lives with the
plugin that owns it:

Per-plugin widgets
------------------

Each plugin's UI lives under its own plugin folder as ``widget/``:

**./plugins/<plugin_name>/widget/**

For example:

- ``./plugins/annotation/widget/``
- ``./plugins/app_color_corrector/widget/``
- ``./plugins/timeline/widget/``

Inside a plugin, import the widget via its top-level plugin name (plugin
folders are added to ``sys.path`` by the plugin manager):

.. code-block:: python

   # in rpa/plugins/annotation/annotation.py
   from annotation.widget.annotation import Annotation

Shared widgets
--------------

Widgets reused by more than one plugin live under a shared folder:

**./plugins/rpa_widgets/**

- ``./plugins/rpa_widgets/sub_widgets/`` — small shared primitives
  (color_circle, slider_toolbar, striped_frame, title_media_editor, …).
- ``./plugins/rpa_widgets/session_io/`` — OTIO session reader/writer; used by
  ``app_session_io`` and ``session_auto_saver``.
- ``./plugins/rpa_widgets/rpa_interpreter/`` — used by ``rpa_interpreter`` and
  ``clips_loop_mode_toggler``.

Import as ``rpa_widgets.<package>.<module>``:

.. code-block:: python

   from rpa_widgets.sub_widgets.slider_toolbar import SliderToolBar
   from rpa_widgets.session_io.session_io import SessionIO

Test harnesses
--------------

Manual-test widgets for RPA APIs live at
**./plugins/rpa_widgets/test_widgets/** alongside the other shared widgets.
They are not loaded as plugins.

=============================
How to create an RPA widget ?
=============================

A plugin widget is just a PySide widget that takes ``rpa`` and a parent
(typically the main window) in its ``__init__``:

.. code-block:: python

   class MyWidget(QtWidgets.QWidget):

      def __init__(self, rpa, main_window):
         super().__init__(main_window)
         self.__rpa = rpa

The plugin's entry-point ``.py`` instantiates the widget inside its
``app_init(self, rpa_app)`` method and parents it to ``rpa_app.main_window``.

================================================
How to make RPA widgets available inside of RV ?
================================================

Plugins are loaded by the RPA plugin manager (see
``./open_rv/pkgs/rpa_widgets_pkg/rpa_widgets_mode.py``). Once a plugin is
listed in the active plugin config (e.g. ``./plugins/open_app_plugins.cfg``),
its widget is created and shown during ``app_init``.
