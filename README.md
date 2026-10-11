# SpinDoctor Qwerty power for Kiro

A [Kiro](https://kiro.dev) **power** (Agent Plugins 1.0.0 layout) that runs the **SpinDoctor 3.1.2 quantum-circuit simulator** on
your computer: `q.*` circuit scripts (1-298 logical qubits), the 241 built-in presets, folders of command files (`q.folder`), and
theory tests from a file, pasted text or the chat itself, each with TXT, PDF, JSON and CSV reports. It brings a local MCP server
(6 tools) and a skill.

> **Honest limits.** SpinDoctor is a classical FP64 simulator. It is not a quantum computer, does not connect to quantum hardware,
> and gives no quantum speed-up or advantage. One entangled group is limited to 59 qubits and dense groups are limited by memory
> (2^n x 16 bytes). Registers wider than 29 qubits sample in basis Z only. Histograms are seeded Born samples.

Version 1.1.0 - engine 1.1.0 (SpinDoctor 3.1.2 parity) - Python 3.8+ as `python3`, standard library only - no network, no account
and no keys for the power itself. **Not tested inside Kiro** (it needs a sign-in); see [Testing](#testing).

## Install

In Kiro: **Powers panel -> Add Custom Power -> Import power from GitHub** and enter
`https://github.com/LKVexa/spindoctor-qwerty-kiro`. Or clone the repo and choose **Import power from a folder** with the clone.

Kiro activates the power when a message mentions one of its keywords (spindoctor, quantum, quantum circuit, qubit, qubits, quantum
simulator, simulator, bell state, ghz, qft, q.circuit, quantum preset, theory test) and then loads the skill and the MCP tools. It
manages the MCP server itself and names it `power-spindoctor-qwerty-spindoctor-qwerty`; nothing is added to
`~/.kiro/settings/mcp.json`.

**Windows / a different Python.** The server starts as `python3`, and the Agent Plugins format allows only one bare executable name
there. If you have no `python3` (python.org installs on Windows give `py` and `python`), make a local copy that uses your command and
import that folder instead:

```bash
py tools/make_local_power.py C:/powers/spindoctor-qwerty --python py       # server starts as: py -3 .../spindoctor_mcp.py
python3 tools/make_local_power.py ~/powers/spindoctor-qwerty --python python3.12
```

## What's in the repo

| Path | What it is |
|---|---|
| `plugin.json` | Power manifest (Agent Plugins 1.0.0): name, version, description, author, keywords, license |
| `mcp.json` | MCP server `spindoctor-qwerty`: `python3 ${PLUGIN_ROOT}/skills/spindoctor-qwerty/scripts/spindoctor_mcp.py` |
| `skills/spindoctor-qwerty/` | Skill (`SKILL.md`), the bundled engine (`spindoctor/`), CLI and MCP server (`scripts/`), examples, LICENSE |
| `tools/make_local_power.py` | Writes a local copy of the power whose server uses another Python command |
| `FUNCTIONS.md` | The full function table with a runnable example for every command |
| `tests/` | Stand-in power host and host check, shared end-to-end suite, reference outputs |

No legacy `POWER.md`, no steering files, no hooks and no credentials: Kiro reads the skill and starts the MCP server, nothing else.

## Using it

- Ask in plain language: "show the SpinDoctor functions", "run a 3-qubit GHZ circuit", "test the Bell state theory we discussed".
- Tools: `spindoctor_functions`, `spindoctor_run_script`, `spindoctor_run_preset`, `spindoctor_list_presets`, `spindoctor_report`,
  `spindoctor_test_theory`.
- The server runs with the installed power folder as its working directory, so give **absolute paths** for files and folders (for a
  #File attachment, its full path on disk). Reports and state go to `~/spindoctor-workspace` unless a call passes `workspace`;
  nothing is written into the power folder.
- Without the tools, the skill tells Kiro to run the same commands with `scripts/spindoctor_cli.py` from the skill folder.

## SpinDoctor Qwerty - plugin tools

| Function | What it does | Command to type |
|---|---|---|
| Function table (spindoctor_functions) | Show this table in chat | Ask: "show the SpinDoctor functions" |
| Run a script (spindoctor_run_script) | Run any q.* lines above; returns results + TXT/JSON/CSV/PDF report paths | Ask: "run q.circuit new bell 2 / q.circuit add h 0 / ..." |
| Run a preset (spindoctor_run_preset) | Run qc-001..qc-241 with overrides | Ask: "run preset qc-067 with shots=64" |
| List presets (spindoctor_list_presets) | Search the 241 presets | Ask: "list presets about Grover" |
| Read a report (spindoctor_report) | List/read TXT reports (PDF/JSON paths alongside) | Ask: "show the newest SpinDoctor report" |
| Test a theory from a file (spindoctor_test_theory source=file) | Read a .txt/.md/.pdf/.py/.json/.csv/.q attachment, then hypothesis -> prediction -> q.* script -> run -> verdict + TXT/PDF theory report | Ask: "test the theory in C:/notes/theory.md" (the host must pass the file path/content) |
| Test a theory from text (spindoctor_test_theory source=text) | Same pipeline for pasted text | Ask: "test this theory: a Hadamard on \|0> gives 50/50" |
| Test the theory we discussed (spindoctor_test_theory source=chat) | The AI summarises the theory from the conversation (claims, assumptions, variables, prediction), you confirm, then it is tested; quoted excerpts go in the report under 'Source: chat history'. An exported chat transcript (.txt/.md/.json/.html) also works | Ask: "test the theory we discussed" or "test the theory in my exported chat C:/chats/conversation.json" |

Every command family is listed with a runnable example in **[FUNCTIONS.md](FUNCTIONS.md)** (the exact table the tool shows):
circuits (`q.circuit`, including 298-qubit wide registers and the `mcx7` gate), queries (`q.query`), the tranche register
(`q.tranche`), the procedural grid, presets and sequences, resource planning, math calculators, physics models, lessons, noise, error
correction, compilation, algorithms, inputs/folders/history (`q.input`, `q.folder`, `q.history`) and the cartridge commands.

## Theory testing

`spindoctor_test_theory` turns a claim into a test: hypothesis -> measurable prediction -> `q.*` script -> run -> compare -> a TXT +
JSON + PDF **theory test report** with the hypothesis, script, raw results, verdict (*supported*, *not supported* or *inconclusive*)
and limits.

- **From a file:** .txt, .md, .pdf, .py, .json, .csv or .q. In Kiro, give the file's absolute path on your computer (for a #File attachment, its full path), or paste the text.
- **From pasted text.**
- **From the chat history:** say *"test the theory we discussed"*. The model writes a short summary (claims, assumptions, variables,
  measurable prediction), shows it to you to confirm or correct, then passes it with optional quoted excerpts; the report records them
  under *Source: chat history*. Exported chat transcripts (.txt/.md/.json/.html from ChatGPT, Claude and others) also work.
- The plugin cannot read your conversation or attachments by itself: only the model sees them, and very long conversations may already
  be truncated by the context window.

Sample theory files and chat transcripts are in `skills/spindoctor-qwerty/examples/theory/`. The two sample
PDFs are stored as text; run `python3 skills/spindoctor-qwerty/examples/theory/make_sample_pdfs.py` to
recreate them.

## Folder ingestion (`q.folder`)

`q.folder run path="<folder>"` runs every supported file at the top level of a folder (.txt, .csv, .json, .qasm, .qasm2, .circuit,
.pdf) in ordinal name order: 1-128 supported files, at most 4 MiB per file, 1-128 commands per file and 4096 characters per command,
strict UTF-8. Other files (for example .md) are skipped and listed. The first failing file stops the job.


## Testing

| Test | Command |
|---|---|
| Stand-in host check (installs this folder) | `python3 tests/kiro_standin_host.py` |
| Same, importing from GitHub | `python3 tests/kiro_standin_host.py --source https://github.com/LKVexa/spindoctor-qwerty-kiro` |
| End-to-end suite only | `python3 tests/e2e_mcp.py --server python3 skills/spindoctor-qwerty/scripts/spindoctor_mcp.py --examples skills/spindoctor-qwerty/examples/theory` |

**Stand-in host, not Kiro.** Kiro (IDE and CLI) needs a sign-in (Builder ID, Google, GitHub or IAM Identity Center), so it was not
run. `tests/kiro_standin_host.py` follows the published rules instead: Kiro's Powers docs (required manifest fields, keyword
activation, `power-<power>-<server>` naming, import from a folder or GitHub) and the Agent Plugins 1.0.0 specification (closed
manifest schema and name rules, skill discovery and frontmatter, the closed stdio server variant, a bare `command` without
placeholders, `${PLUGIN_ROOT}`/`${PLUGIN_DATA}` expansion, `PLUGIN_ROOT`/`PLUGIN_DATA` in the server's environment, the power root as
working directory, containment). To show it enforces those rules it first rejects eight deliberately broken variants. Then it
installs the power into a throwaway home, checks that an unrelated message does not activate it and a keyword message does, starts
the server exactly as configured, calls all 6 tools (function table, a Bell circuit, qc-001, a 298-qubit `mcx7` circuit, a theory
from a file and from the chat: verdict *supported*, PDF written), checks the power folder is unchanged, runs every CLI command in
SKILL.md, checks `make_local_power.py`, and runs the shared end-to-end suite through the installed server. Not tested: Kiro's real
UI, installer and folders, a real model choosing the tools, Windows, macOS. Results: [E2E_RESULTS.md](E2E_RESULTS.md).

## Author and license

Author: **RUSSELL PHILIP SMITHSON** <russellsmithson77@outlook.com>

Copyright (C) 2026 RUSSELL PHILIP SMITHSON. Licensed under the GNU General Public License v3.0 or later (`GPL-3.0-or-later`): see
[LICENSE](LICENSE), [NOTICE](NOTICE) and [COPYRIGHT](COPYRIGHT). Kiro is an AWS product; this power is not affiliated with AWS or
Kiro.
