# Require click for AMBOSS tooltip

Install the Anki addon from [AnkiWeb](https://ankiweb.net/shared/info/354696931).

## Description

🔎 Disable AMBOSS tooltips on hover and require a click instead.

![Demonstration showing how AMBOSS tooltips require a click instead of hover](https://github.com/qais8r/anki-require-click-for-amboss-tooltip/blob/main/assets/demo.gif?raw=true)

This add‑on hooks into the reviewer and patches AMBOSS’s tooltip trigger at runtime, so definitions no longer pop up on hover and are shown only when you click a highlighted term.

## Changelog

- **Version 1.0** — Initial version that forces AMBOSS tooltips to trigger on click instead of hover by modifying `tippyOptions` and root tooltip props.
- **Version 1.1** — Added broader patching: updates existing tooltip instances, delegate options, retries initialization, and scans DOM elements for active tooltips.
- **Version 1.2** — Major robustness upgrade with full manager patching, click-gate logic, outside-click closing, animation-aware hiding, controller interception, and multi-fallback compatibility handling.
