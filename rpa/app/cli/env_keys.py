"""
Env-var names shared between the pre-rv launcher (launch_app.py) and the
in-rvpkg Controller. Single source of truth so a rename only touches one file.
"""

# JSON-serialized argparse.Namespace set by launch_app.py, read by
# Controller.__init__ and rehydrated into an argparse.Namespace for plugins.
RPA_APP_CLI_ARGS_JSON = "RPA_APP_CLI_ARGS_JSON"
