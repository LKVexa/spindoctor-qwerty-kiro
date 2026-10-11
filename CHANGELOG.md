# Changelog

## 1.1.0 - 2026-10-11

- Engine 1.1.0 at parity with the updated SpinDoctor 3.1.2: 1-298 logical qubits (59 per entangled factor), the `mcx7` gate,
  wide-register Born-Z sampling, `q.folder` with 3.1.2 semantics, CSV report copies and measurement-CSV fitting equations. All 241
  presets replayed. Tools `spindoctor_functions` (function table, marked read-only) and `spindoctor_test_theory` (theory testing
  from a file, pasted text or the chat, with TXT+JSON+PDF theory reports). 1.0 described SpinDoctor 3.0.3 and a 29-qubit cap.
- **The repo root is the power.** `plugin.json`, `mcp.json` and `skills/` sit at the top, so "Import power from GitHub" takes the
  plain repository URL. 1.0 kept the power in a `spindoctor-qwerty/` subfolder.
- **Keywords that match how people ask.** Kiro activates a power when a message mentions one of its keywords. 1.0 used `mcp`,
  `presets` and `qwerty`, so any message about MCP servers would pull in a quantum simulator, while "Bell state", "GHZ", "QFT" or
  "quantum circuit" would not. 1.1.0: spindoctor, quantum, quantum circuit, qubit(s), quantum simulator, simulator, bell state, ghz,
  qft, q.circuit, quantum preset, theory test.
- **Reports in one place.** 1.0 pointed the server's workspace at a `workspace` folder inside `${PLUGIN_DATA}` (Kiro-managed, one you would not
  normally browse) while the shell fallback used `~/spindoctor-workspace`. Both now use `~/spindoctor-workspace` (or a `workspace`
  argument / `--workspace`). mcp.json sets only `PYTHONUTF8` and `PYTHONDONTWRITEBYTECODE`, so the installed power folder stays
  unchanged.
- **Windows / other Pythons.** The Agent Plugins format allows one bare executable name as the server `command`, and the power uses
  `python3`. `tools/make_local_power.py OUT --python py` (or `python`) writes a local copy whose mcp.json uses that command (`py -3`
  for the Windows launcher); import that folder instead.
- SKILL.md: names Kiro's server (`power-spindoctor-qwerty-spindoctor-qwerty`), says to pass absolute paths (the server runs in the
  power folder; for a #File attachment give its full path), describes the shell fallback from the skill folder, uses bundled files
  only in its examples (`examples/theory/xbasis.q`, new `examples/bell_theory_args.json`; every one runs as written), and adds
  `compatibility`; the skill folder carries its own LICENSE.
- plugin.json: author name and email, homepage, repository, license GPL-3.0-or-later.
- Tests: `tests/kiro_standin_host.py`, a stand-in power host built from Kiro's Powers docs and the Agent Plugins 1.0.0 spec (Kiro
  itself needs a sign-in, so it is not run).
- License changed from MIT to GPL-3.0-or-later. Author RUSSELL PHILIP SMITHSON. README, NOTICE, COPYRIGHT and SPDX headers added.

## 1.0.0

- First release: `spindoctor-qwerty/` folder in the Agent Plugins layout (plugin.json, mcp.json, skill), engine described as
  SpinDoctor 3.0.3.
