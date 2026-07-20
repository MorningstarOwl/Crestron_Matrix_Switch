"""Constants for the Crestron HD-MD Matrix Switch integration."""

from __future__ import annotations

DOMAIN = "crestron_hd_md"

DEFAULT_PORT = 23
DEFAULT_INPUTS = 4
DEFAULT_OUTPUTS = 2

CONF_INPUTS = "inputs"
CONF_OUTPUTS = "outputs"

# Option keys are generated dynamically: input_name_1, output_name_1, ...
OPT_INPUT_NAME = "input_name_{}"
OPT_OUTPUT_NAME = "output_name_{}"

# Route number 0 means "nothing routed" on the device.
ROUTE_NONE = 0
OPTION_NONE = "None"

SCAN_INTERVAL_SECONDS = 30
