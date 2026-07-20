# Crestron HD-MD Matrix Switch for Home Assistant

A Home Assistant custom integration for Crestron **HD-MD series** HDMI
switchers (tested on the **HD-MD4X2-4K-E**, and expected to work on the
HD-MD6X2-4K-E, HD-MD4X1-4K-E and similar models with a telnet console).

No Crestron control processor required — the integration talks directly to
the switcher's built-in telnet console over your LAN.

## Features

- One **select** (dropdown) entity per HDMI output to choose its source
- Friendly, configurable names for every input and output (Options flow)
- Polls the switcher every 30 seconds, so routing changes made from the
  front panel or web interface show up in Home Assistant
- Instant state updates when routing from Home Assistant (the switcher
  confirms every route change)
- Fully local — no cloud, no extra dependencies

## Requirements

- The switcher connected to your network with a known IP address
  (a DHCP reservation or static IP is recommended)
- The telnet console reachable on port 23 (enabled by default). You can
  verify with PuTTY or `telnet <ip> 23` — you should see
  `Welcome to TELNET.` and a `>` prompt.

> **Note:** the switcher only allows a limited number of simultaneous
> telnet sessions. If setup fails, make sure nothing else (PuTTY, a
> script) is holding the console open.

## Installation

### HACS (recommended)

1. In HACS, open the **⋮** menu → **Custom repositories**
2. Add `https://github.com/MorningstarOwl/Crestron_Matrix_Switch` with
   type **Integration**
3. Search for "Crestron HD-MD Matrix Switch" in HACS and install it
4. Restart Home Assistant

### Manual

Copy `custom_components/crestron_hd_md` into your Home Assistant
`config/custom_components/` folder and restart.

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Crestron HD-MD Matrix Switch**
3. Enter the switcher's IP address, port (23), and the number of
   inputs/outputs (an HD-MD4X2 is 4 in / 2 out — Crestron model names
   are `<inputs>X<outputs>`)
4. Optional: open the integration's **Configure** dialog to give your
   inputs and outputs real names ("Apple TV", "Living Room TV", ...)

You get one entity per output, e.g. `select.hd_md_192_168_4_99_output_1`.
Choosing **None** blanks the output.

## Using it in automations

```yaml
# Example: route the Xbox to the living room TV when it powers on
automation:
  - alias: "Xbox on -> living room"
    triggers:
      - trigger: device
        # ... your Xbox power-on trigger ...
    actions:
      - action: select.select_option
        target:
          entity_id: select.hd_md_192_168_4_99_output_1
        data:
          option: "Xbox"
```

## How it works

The HD-MD series exposes a plain-text console on TCP port 23:

```
> show output 1 route
event output 1 route 4

> conf output 1 route 2
event output 1 route 2
```

Route `0` means nothing is routed. This integration opens a short-lived
telnet session per poll/command (serialized with a lock) so it never
exhausts the switcher's limited session pool.

Protocol details were confirmed against a real HD-MD4X2-4K-E; thanks to
[will2hew/homebridge-crestron-md4x2](https://github.com/will2hew/homebridge-crestron-md4x2)
for the original discovery that these units accept console routing
commands.

## License

[MIT](LICENSE)
