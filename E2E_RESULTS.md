# E2E results - spindoctor-qwerty-kiro 1.1.0

Host: **stand-in power host** (`tests/kiro_standin_host.py`), built from Kiro's Powers docs and the Agent Plugins 1.0.0
specification. Kiro (IDE and CLI) needs a sign-in, so it was not run. The stand-in validates the manifest, skill and mcp.json by
those rules (and first rejects eight broken variants), installs the power into a throwaway home, activates it by keyword, starts the
power's own MCP server exactly as mcp.json configures it (`${PLUGIN_ROOT}` expanded, `PLUGIN_ROOT`/`PLUGIN_DATA` set, power root as
working directory) and speaks MCP to it. Python 3.13.5.

Not tested: Kiro's real UI, installer and folders, a real model choosing the tools, Windows, macOS.

## Host check: 24/24

| Result | Check |
|---|---|
| PASS | plugin.json: Kiro-required fields, version 1.1.0, GPL-3.0-or-later, author with name/email, homepage/repository, >= 8 keywords |
| PASS | every .py file has a GPL-3.0-or-later SPDX header (26 files) |
| PASS | no symlinks in the package (containment rule) |
| PASS | SKILL.md: guardrail, Kiro server name, absolute-path rule, no other host's variables |
| PASS | shell fallback: every CLI command in SKILL.md runs as written from the skill folder (6 commands, bundled files only) |
| PASS | stand-in loader refuses 4 bad manifests (uppercase name, extra author field, no keywords, unknown $schema) and skips 4 bad servers (shell-string command, env PLUGIN_ROOT, absolute cwd, unknown field) |
| PASS | import power from a folder: manifest valid, no loader warnings |
| PASS | discovered 1 skill (spindoctor-qwerty) and 1 stdio server, namespaced power-spindoctor-qwerty-spindoctor-qwerty |
| PASS | a message without a keyword does not activate the power (no server started) |
| PASS | keyword message ('bell state', 'qubits') activates the power and starts its server |
| PASS | server started as configured: python3 with ${PLUGIN_ROOT} expanded, cwd = power root, MCP initialize ok |
| PASS | tools/list returns the 6 SpinDoctor tools (spindoctor_functions marked read-only) |
| PASS | spindoctor_functions: the Markdown function table |
| PASS | spindoctor_run_script: Bell circuit ok, reports under ~/spindoctor-workspace |
| PASS | spindoctor_run_preset qc-001 ok |
| PASS | spindoctor_list_presets ghz ok |
| PASS | spindoctor_report lists the newest reports |
| PASS | 298-qubit wide register with mcx7 runs (3.1.2 parity) |
| PASS | theory extract from an absolute file path (as with #File) |
| PASS | spindoctor_test_theory from the chat: supported, 2 excerpts, valid PDF |
| PASS | installed power folder unchanged by tool use (no __pycache__, reports outside) |
| PASS | tools/make_local_power.py makes a valid power copy with the chosen Python command |
| PASS | make_local_power.py --python py writes command py with args [-3, server] (Windows launcher) |
| PASS | shared end-to-end suite through the installed power's server: SUMMARY 12/12 passed in 12.9s |

## Shared end-to-end suite through the installed power: 12/12

Started as the stand-in starts the power's server: `python3 <installed power>/skills/spindoctor-qwerty/scripts/spindoctor_mcp.py`.

| Result | Check |
|---|---|
| PASS | initialize (server spindoctor-qwerty 1.1.0) |
| PASS | tools/list exposes the 6 tools |
| PASS | function table (Markdown, 19 sections, 298-qubit limits listed) |
| PASS | 241 presets listed |
| PASS | one script per command family (16 families, every table example) |
| PASS | 298-qubit circuit with mcx7 (prepared-factor-Born-Z) |
| PASS | q.folder on mixed .txt/.csv/.json/.qasm folder (+ .md skipped) |
| PASS | theory from a file -> supported, TXT+PDF report |
| PASS | theory from a chat summary + quoted excerpts -> supported |
| PASS | theory from an exported chat transcript -> supported |
| PASS | presets qc-001..qc-025 match the updated 3.1.2 reference (20 identical, 5 documented differences) |
| PASS | TXT+PDF reports valid (255 PDFs, 255 TXT twins) |

## Runs

- Pre-push (box, 2026-10-11): stand-in host check 24/24, importing the staged folder.
