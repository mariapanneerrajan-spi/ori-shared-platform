"""
Env-var names shared between the pre-rv launcher (launch_itview.py) and the
in-rvpkg Controller. Single source of truth so a rename only touches one file.
"""

# JSON-serialized argparse.Namespace set by launch_itview.py, read by
# Controller.__init__ and rehydrated into an argparse.Namespace for plugins.
ITVIEW5_CLI_ARGS_JSON = "ITVIEW5_CLI_ARGS_JSON"
