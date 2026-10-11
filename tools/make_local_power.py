#!/usr/bin/env python3
# SpinDoctor Qwerty 1.1.0 - SpinDoctor Qwerty power for Kiro: make a local copy that starts the MCP server with another Python
# Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>
# SPDX-License-Identifier: GPL-3.0-or-later
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version. It is distributed WITHOUT ANY WARRANTY; see the LICENSE file for details.
"""Copy this power to OUT_DIR with mcp.json starting the server through a Python command you choose.

The power's mcp.json starts the server as `python3`. Windows (python.org installer: `py` / `python`) and some other systems have no
`python3`. The Agent Plugins format allows only one bare executable name in `command` (no placeholders, no shell string), so instead
of editing your clone, make a local copy and import that folder in Kiro (Powers -> Add Custom Power -> Import power from a folder):

  py tools/make_local_power.py OUT_DIR                    # uses `py -3` on Windows, else the name of the Python running this
  py tools/make_local_power.py OUT_DIR --python python    # or any bare command on PATH: py | python | python3
  python3 tools/make_local_power.py OUT_DIR --python python3.12

OUT_DIR must not exist yet. Only plugin.json, mcp.json, skills/, LICENSE, NOTICE, COPYRIGHT and README.md are copied, and only the
`command` (and a leading `-3` for `py`) changes. Standard library only.
"""
import json, os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEEP = ("plugin.json", "mcp.json", "skills", "LICENSE", "NOTICE", "COPYRIGHT", "README.md")


def main():
    a = sys.argv[1:]
    if not a or "-h" in a or "--help" in a:
        print(__doc__); return 0 if a else 2
    out = os.path.abspath(a[0]); opt = dict(zip(a[1::2], a[2::2]))
    py = opt.get("--python") or ("py" if os.name == "nt" else os.path.basename(sys.executable))
    if os.sep in py or "/" in py or " " in py:
        print("--python must be a bare command name on PATH (Agent Plugins `command` rule), e.g. py, python, python3"); return 2
    if os.path.exists(out):
        print("already exists: %s (choose a new folder)" % out); return 1
    os.makedirs(out)
    for name in KEEP:
        src = os.path.join(ROOT, name)
        if os.path.isdir(src): shutil.copytree(src, os.path.join(out, name), ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        elif os.path.isfile(src): shutil.copy2(src, os.path.join(out, name))
    p = os.path.join(out, "mcp.json"); cfg = json.load(open(p, encoding="utf-8"))
    srv = cfg["mcpServers"]["spindoctor-qwerty"]
    args = [x for x in srv.get("args", []) if x != "-3"]
    srv["command"] = py; srv["args"] = (["-3"] if py.lower() in ("py", "py.exe") else []) + args
    with open(p, "w", encoding="utf-8", newline="\n") as f: json.dump(cfg, f, indent=2); f.write("\n")
    print("made %s (MCP server command: %s %s)" % (out, py, " ".join(srv["args"])))
    print("Import it in Kiro: Powers -> Add Custom Power -> Import power from a folder -> %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
