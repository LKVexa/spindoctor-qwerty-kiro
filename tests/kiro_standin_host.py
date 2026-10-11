#!/usr/bin/env python3
# SpinDoctor Qwerty 1.1.0 - SpinDoctor Qwerty power for Kiro: stand-in power host and host check
# Copyright (C) 2026 RUSSELL PHILIP SMITHSON <russellsmithson77@outlook.com>
# SPDX-License-Identifier: GPL-3.0-or-later
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General
# Public License as published by the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version. It is distributed WITHOUT ANY WARRANTY; see the LICENSE file for details.
"""Stand-in Kiro power host. Run from the repo root:

  python3 tests/kiro_standin_host.py                                   # install this folder, activate, call every tool
  python3 tests/kiro_standin_host.py --source https://github.com/LKVexa/spindoctor-qwerty-kiro   # "Import power from GitHub"

Kiro (IDE and CLI) needs a sign-in (Builder ID, Google, GitHub or Identity Center), so it is not run here. This script follows the
published rules instead: Kiro's Powers docs (kiro.dev/docs/powers/create and /installation: plugin.json with $schema, name, version,
description, author.name and keywords; optional skills/ and mcp.json; server names namespaced as power-<power>-<server>; activation
when a message mentions a keyword; import from a folder or from a GitHub URL) and the Agent Plugins 1.0.0 specification (closed
manifest schema, name rules, fixed component locations, Agent Skills frontmatter, closed stdio server variant, bare or ./ command,
no placeholders in command, ${PLUGIN_ROOT}/${PLUGIN_DATA} expansion in args/env/cwd, PLUGIN_ROOT/PLUGIN_DATA in the subprocess
environment, plugin root as default cwd, containment). It speaks MCP over stdio to the power's own server exactly as configured.
What it cannot show: Kiro's real UI, its model choosing tools, its actual install folders, Windows/macOS. Standard library only.
"""
import json, os, re, shutil, subprocess, sys, tempfile
sys.dont_write_bytecode = True; os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
PSCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"; MSCHEMA = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
TOOLS = ["spindoctor_functions", "spindoctor_list_presets", "spindoctor_report", "spindoctor_run_preset", "spindoctor_run_script", "spindoctor_test_theory"]
R = []
OK = lambda s: bool(re.search(r'"ok":\s*true', s or ""))


def T(name, ok, detail=""):
    R.append({"check": name, "pass": bool(ok), "detail": str(detail)[:600]})
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else "  -- " + str(detail)[:500])); sys.stdout.flush()


# ---------------------------------------------------------------- loader (Agent Plugins 1.0.0 + Kiro Powers docs)
def inside(root, p):
    r = os.path.realpath(root); q = os.path.realpath(p)
    return q == r or q.startswith(r + os.sep)


def valid_name(n):
    return isinstance(n, str) and 1 <= len(n) <= 64 and re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", n) and "--" not in n and ".." not in n


def frontmatter(text):
    if not text.startswith("---\n"): return None
    end = text.find("\n---", 4)
    if end < 0: return None
    out, cur = {}, None
    for ln in text[4:end].splitlines():
        if not ln.strip(): continue
        if ln.startswith("  ") and cur == "metadata":
            k, _, v = ln.strip().partition(":"); out["metadata"][k.strip()] = v.strip().strip('"'); continue
        k, _, v = ln.partition(":"); k = k.strip(); v = v.strip(); cur = k
        out[k] = {} if (k == "metadata" and not v) else v.strip('"')
    return out


def load_power(root):
    """Return (power dict, errors). Fatal manifest errors -> power None (plugin rejected)."""
    errs = []; mp = os.path.join(root, "plugin.json")
    if not os.path.isfile(mp) or not inside(root, mp): return None, ["no plugin.json in the power root"]
    try: m = json.load(open(mp, encoding="utf-8"))
    except ValueError as e: return None, ["plugin.json is not JSON: %s" % e]
    if not isinstance(m, dict): return None, ["plugin.json is not an object"]
    allowed = {"$schema", "name", "version", "description", "author", "homepage", "repository", "license", "keywords", "extensions"}
    for k in set(m) - allowed: errs.append("unknown manifest field ignored: %s" % k)
    if m.get("$schema") != PSCHEMA: return None, ["unsupported $schema %r" % m.get("$schema")]
    if not valid_name(m.get("name")): return None, ["invalid name %r" % m.get("name")]
    for k in ("version", "description", "homepage", "repository", "license"):
        if k in m and not isinstance(m[k], str): return None, ["%s must be a string" % k]
    a = m.get("author")
    if a is not None and (not isinstance(a, dict) or set(a) - {"name", "email", "url"} or not all(isinstance(v, str) for v in a.values())):
        return None, ["author must be an object with only string name/email/url"]
    kw = m.get("keywords")
    if kw is not None and (not isinstance(kw, list) or not all(isinstance(x, str) for x in kw)): return None, ["keywords must be a string array"]
    # Kiro's Powers docs list these as required for a power
    for k in ("version", "description", "keywords"):
        if not m.get(k): return None, ["Kiro power requires %s" % k]
    if not (a and a.get("name")): return None, ["Kiro power requires author.name"]
    p = {"root": root, "manifest": m, "name": m["name"], "skills": {}, "servers": {}, "errors": errs}
    sd = os.path.join(root, "skills")
    if os.path.isdir(sd) and inside(root, sd):
        for d in sorted(os.listdir(sd)):
            f = os.path.join(sd, d, "SKILL.md")
            if not os.path.isfile(f) or not inside(root, f): continue
            text = open(f, encoding="utf-8").read(); fm = frontmatter(text) or {}
            n = fm.get("name", ""); desc = fm.get("description", "")
            bad = []
            if n != d or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", n or "-") or len(n) > 64: bad.append("name must equal the folder and be lowercase-hyphen <= 64")
            if not desc or len(desc) > 1024: bad.append("description 1..1024 chars")
            if len(fm.get("compatibility", "")) > 500: bad.append("compatibility > 500 chars")
            if "metadata" in fm and not isinstance(fm["metadata"], dict): bad.append("metadata must be a map")
            if bad: errs.append("skill %s skipped: %s" % (d, "; ".join(bad))); continue
            p["skills"][n] = {"dir": os.path.join(sd, d), "frontmatter": fm, "body": text}
    mj = os.path.join(root, "mcp.json")
    if os.path.isfile(mj) and inside(root, mj):
        try: c = json.load(open(mj, encoding="utf-8"))
        except ValueError: c = None
        if not isinstance(c, dict) or set(c) != {"$schema", "mcpServers"} or c["$schema"] != MSCHEMA or not isinstance(c["mcpServers"], dict):
            errs.append("mcp.json invalid: MCP disabled for this power")
        else:
            for sname, s in c["mcpServers"].items():
                why = server_problem(root, s)
                if why: errs.append("server %s skipped: %s" % (sname, why)); continue
                p["servers"]["power-%s-%s" % (m["name"], sname)] = s
    return p, errs


def server_problem(root, s):
    if not isinstance(s, dict) or s.get("type") != "stdio": return "only the stdio variant is used by this stand-in"
    if set(s) - {"type", "command", "args", "env", "cwd"}: return "unknown field(s) %s" % sorted(set(s) - {"type", "command", "args", "env", "cwd"})
    cmd = s.get("command")
    if not isinstance(cmd, str) or not cmd or " " in cmd or "${" in cmd: return "command must be one executable token without placeholders"
    if cmd.startswith("./"):
        if not inside(root, os.path.join(root, cmd)): return "command escapes the power root"
    elif "/" in cmd or "\\" in cmd: return "command must be a bare name or ./path"
    if "args" in s and (not isinstance(s["args"], list) or not all(isinstance(x, str) for x in s["args"])): return "args must be strings"
    env = s.get("env", {})
    if not isinstance(env, dict) or not all(isinstance(v, str) for v in env.values()): return "env must map strings"
    if {"PLUGIN_ROOT", "PLUGIN_DATA"} & {k.upper() for k in env}: return "env must not set PLUGIN_ROOT/PLUGIN_DATA"
    cwd = s.get("cwd")
    if cwd is not None and not (cwd.startswith("./") or cwd == "${PLUGIN_ROOT}" or cwd.startswith("${PLUGIN_ROOT}/") or cwd == "${PLUGIN_DATA}" or cwd.startswith("${PLUGIN_DATA}/")):
        return "cwd form not allowed"
    return None


class Host:
    """Throwaway Kiro-like home: installs powers, activates them by keyword, runs their MCP servers."""
    def __init__(self):
        self.home = tempfile.mkdtemp(prefix="sdq_kiro_"); self.installed = {}; self.active = {}
        self.inst = os.path.join(self.home, ".kiro", "powers", "installed"); self.data = os.path.join(self.home, ".kiro", "powers", "data")
        os.makedirs(self.inst); os.makedirs(self.data)
        self.env = dict(os.environ, HOME=self.home, USERPROFILE=self.home); self.env.pop("SPINDOCTOR_WORKSPACE", None)

    def install(self, src):
        """Import power from a folder (path) or from GitHub (https URL)."""
        if re.match(r"https://github\.com/", src):
            tmp = os.path.join(self.home, "clone"); subprocess.run(["git", "clone", "-q", "--depth", "1", src, tmp], check=True)
            src = tmp
        p, errs = load_power(src)
        if p is None: return None, errs
        dst = os.path.join(self.inst, p["name"]); shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
        p, errs = load_power(dst); self.installed[p["name"]] = p; return p, errs

    def activate(self, message):
        """Kiro loads a power's skills and MCP tools when a message mentions one of its keywords."""
        hit = []
        for n, p in self.installed.items():
            words = [k.lower() for k in p["manifest"].get("keywords", [])]
            if any(re.search(r"(?<![a-z0-9])" + re.escape(w) + r"(?![a-z0-9])", message.lower()) for w in words):
                if n not in self.active: self.active[n] = {s: Mcp(p, s, cfg, self) for s, cfg in p["servers"].items()}
                hit.append(n)
        return hit

    def close(self):
        for srv in self.active.values():
            for m in srv.values(): m.close()
        self.active = {}


def expand(v, root, data):
    return v.replace("${PLUGIN_ROOT}", root).replace("${PLUGIN_DATA}", data)


class Mcp:
    def __init__(self, p, name, cfg, host):
        root = os.path.realpath(p["root"]); data = os.path.join(host.data, p["name"]); os.makedirs(data, exist_ok=True)
        cmd = cfg["command"]; cmd = os.path.join(root, cmd[2:]) if cmd.startswith("./") else (shutil.which(cmd) or cmd)
        env = dict(host.env); env.update({k: expand(v, root, data) for k, v in cfg.get("env", {}).items()})
        env["PLUGIN_ROOT"] = root; env["PLUGIN_DATA"] = data
        cwd = expand(cfg.get("cwd", "${PLUGIN_ROOT}"), root, data); cwd = os.path.join(root, cwd[2:]) if cwd.startswith("./") else cwd
        self.argv = [cmd] + [expand(a, root, data) for a in cfg.get("args", [])]; self.name = name; self.cwd = cwd
        self.proc = subprocess.Popen(self.argv, cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, encoding="utf-8")
        self.n = 0
        self.init = self.rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "kiro-standin", "version": "1.1.0"}})
        self.proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n"); self.proc.stdin.flush()
        self.tools = {t["name"]: t for t in (self.rpc("tools/list", {}).get("result", {}).get("tools", []))}

    def rpc(self, method, params):
        self.n += 1; self.proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": self.n, "method": method, "params": params}) + "\n"); self.proc.stdin.flush()
        while True:
            line = self.proc.stdout.readline()
            if not line: return {"error": "server closed"}
            try: msg = json.loads(line)
            except ValueError: continue
            if msg.get("id") == self.n: return msg

    def call(self, tool, args):
        r = self.rpc("tools/call", {"name": tool, "arguments": args}).get("result", {})
        return "\n".join(c.get("text", "") for c in r.get("content", []) if c.get("type") == "text")

    def close(self):
        try: self.proc.stdin.close(); self.proc.wait(timeout=10)
        except Exception: self.proc.kill()


# ---------------------------------------------------------------- checks
def negative():
    """The loader must refuse what Kiro / Agent Plugins refuse (so a pass below means something)."""
    base = tempfile.mkdtemp(prefix="sdq_kiro_neg_"); src = os.path.join(base, "p")
    shutil.copytree(ROOT, src, ignore=shutil.ignore_patterns(".git", "__pycache__", "tests", "examples", "spindoctor"))
    m = json.load(open(os.path.join(src, "plugin.json"))); c = json.load(open(os.path.join(src, "mcp.json")))
    def with_(mm=None, cc=None):
        json.dump(mm or m, open(os.path.join(src, "plugin.json"), "w")); json.dump(cc or c, open(os.path.join(src, "mcp.json"), "w"))
        return load_power(src)
    bad = 0
    for mm in ({**m, "name": "SpinDoctor"}, {**m, "author": {"name": "x", "company": "y"}}, {k: v for k, v in m.items() if k != "keywords"}, {**m, "$schema": "https://example.com/x.json"}):
        bad += with_(mm)[0] is None
    srv = c["mcpServers"]["spindoctor-qwerty"]
    for s in ({**srv, "command": "python3 -u"}, {**srv, "env": {"PLUGIN_ROOT": "/x"}}, {**srv, "cwd": "/tmp"}, {**srv, "timeout": 5}):
        p, _ = with_(m, {**c, "mcpServers": {"spindoctor-qwerty": s}}); bad += bool(p) and not p["servers"]
    shutil.rmtree(base, ignore_errors=True)
    T("stand-in loader refuses 4 bad manifests (uppercase name, extra author field, no keywords, unknown $schema) and skips 4 bad servers (shell-string command, env PLUGIN_ROOT, absolute cwd, unknown field)", bad == 8, bad)


def static():
    m = json.load(open(os.path.join(ROOT, "plugin.json"), encoding="utf-8"))
    T("plugin.json: Kiro-required fields, version 1.1.0, GPL-3.0-or-later, author with name/email, homepage/repository, >= 8 keywords",
      m.get("version") == "1.1.0" and m.get("license") == "GPL-3.0-or-later" and m["author"].get("name") == "RUSSELL PHILIP SMITHSON"
      and m.get("repository", "").endswith("/spindoctor-qwerty-kiro") and len(m.get("keywords", [])) >= 8 and "spindoctor" in m["keywords"], m)
    py = [os.path.join(d, f) for d, _, fs in os.walk(ROOT) if "/.git" not in d and "__pycache__" not in d for f in fs if f.endswith(".py")]
    bad = [x for x in py if "SPDX-License-Identifier: GPL-3.0-or-later" not in open(x, encoding="utf-8").read(2500)]
    T("every .py file has a GPL-3.0-or-later SPDX header (%d files)" % len(py), not bad, bad[:3])
    links = [os.path.join(d, f) for d, ds, fs in os.walk(ROOT) for f in fs + ds if os.path.islink(os.path.join(d, f))]
    T("no symlinks in the package (containment rule)", not links, links)
    sk = os.path.join(ROOT, "skills", "spindoctor-qwerty"); t = open(os.path.join(sk, "SKILL.md"), encoding="utf-8").read()
    T("SKILL.md: guardrail, Kiro server name, absolute-path rule, no other host's variables", "not a\nquantum computer" in t
      and "power-spindoctor-qwerty-spindoctor-qwerty" in t and "ABSOLUTE paths" in t and not re.search(r"\$\{[A-Z_]+\}", t))
    cmds = [ln.split("  #")[0].strip() for blk in re.findall(r"```bash\n(.*?)```", t, re.S) for ln in blk.splitlines() if ln.startswith("python3 scripts/")]
    ws = tempfile.mkdtemp(prefix="sdq_cli_"); bad = []
    for c in cmds:
        argv = c.split(" ", 2); rest = re.findall(r'"[^"]*"|\S+', argv[2])
        r = subprocess.run([sys.executable, argv[1], "--workspace", ws] + [x.strip('"') for x in rest], cwd=sk, capture_output=True, timeout=300)
        if r.returncode: bad.append((c, r.stderr[-200:]))
    T("shell fallback: every CLI command in SKILL.md runs as written from the skill folder (%d commands, bundled files only)" % len(cmds), cmds and not bad, bad)
    shutil.rmtree(ws, ignore_errors=True)
    negative()


def standin(source):
    h = Host()
    try:
        p, errs = h.install(source or ROOT)
        T("import power from %s: manifest valid, no loader warnings" % ("GitHub (" + source + ")" if source else "a folder"), p is not None and not errs, errs)
        if not p: return
        T("discovered 1 skill (spindoctor-qwerty) and 1 stdio server, namespaced power-spindoctor-qwerty-spindoctor-qwerty",
          list(p["skills"]) == ["spindoctor-qwerty"] and list(p["servers"]) == ["power-spindoctor-qwerty-spindoctor-qwerty"], (list(p["skills"]), list(p["servers"])))
        T("a message without a keyword does not activate the power (no server started)", h.activate("refactor this function please") == [] and not h.active)
        hit = h.activate("Can you simulate a Bell state with qubits?")
        srv = h.active.get("spindoctor-qwerty", {}).get("power-spindoctor-qwerty-spindoctor-qwerty")
        T("keyword message ('bell state', 'qubits') activates the power and starts its server", hit == ["spindoctor-qwerty"] and srv is not None, hit)
        if not srv: return
        root = os.path.realpath(p["root"])
        T("server started as configured: python3 with ${PLUGIN_ROOT} expanded, cwd = power root, MCP initialize ok",
          srv.argv[1] == os.path.join(root, "skills", "spindoctor-qwerty", "scripts", "spindoctor_mcp.py") and srv.cwd == root and "serverInfo" in json.dumps(srv.init), srv.argv)
        T("tools/list returns the 6 SpinDoctor tools (spindoctor_functions marked read-only)", sorted(srv.tools) == TOOLS
          and (srv.tools.get("spindoctor_functions", {}).get("annotations") or {}).get("readOnlyHint") is True, sorted(srv.tools))
        r = srv.call("spindoctor_functions", {})
        T("spindoctor_functions: the Markdown function table", "| Function | What it does | Command to type |" in r, r[:150])
        r = srv.call("spindoctor_run_script", {"script": "q.circuit new bell 2\nq.circuit add h 0\nq.circuit add cx 0 1\nq.circuit run shots 1000 basis z"})
        T("spindoctor_run_script: Bell circuit ok, reports under ~/spindoctor-workspace", OK(r) and os.path.join(h.home, "spindoctor-workspace") in r, r[:200])
        r = srv.call("spindoctor_run_preset", {"preset_id": "qc-001"}); T("spindoctor_run_preset qc-001 ok", OK(r) and "qc-001" in r, r[:200])
        r = srv.call("spindoctor_list_presets", {"filter": "ghz"}); T("spindoctor_list_presets ghz ok", OK(r) and "ghz" in r.lower(), r[:200])
        r = srv.call("spindoctor_report", {}); T("spindoctor_report lists the newest reports", OK(r) and ".txt" in r, r[:200])
        r = srv.call("spindoctor_run_script", {"script": "q.circuit new big 298\nq.circuit add h 0\nq.circuit add mcx7 0 1 2 3 4 5 6 297\nq.circuit run shots 64 basis z"})
        T("298-qubit wide register with mcx7 runs (3.1.2 parity)", OK(r), r[:200])
        th = os.path.join(root, "skills", "spindoctor-qwerty", "examples", "theory", "hadamard_theory.txt")
        r = srv.call("spindoctor_test_theory", {"action": "extract", "source": "file", "path": th}); T("theory extract from an absolute file path (as with #File)", OK(r), r[:200])
        r = srv.call("spindoctor_test_theory", {"action": "run", "source": "chat",
              "text": "From our chat: H then CX makes a Bell state, so 00 and 11 each appear about half the time.",
              "excerpts": ["User: does H then CNOT give 50/50 on 00 and 11?", "Assistant: yes, that is a Bell state."],
              "hypothesis": "H(0) then CX(0,1) gives P(00) = P(11) = 0.5", "prediction": "P(11) = 0.5 +/- 0.05 over 4000 shots",
              "script": "q.circuit new bt 2\nq.circuit add h 0\nq.circuit add cx 0 1\nq.circuit run shots 4000 basis z",
              "checks": [{"kind": "probability", "outcome": "11", "expected": 0.5, "tolerance": 0.05}]})
        pdf = re.findall(r'"([^"]+theory[^"]*\.pdf)"', r)
        T("spindoctor_test_theory from the chat: supported, 2 excerpts, valid PDF", '"verdict": "supported"' in r and '"excerptsRecorded": 2' in r
          and pdf and open(pdf[0], "rb").read(5) == b"%PDF-", r[:300])
        before = sorted(os.path.relpath(os.path.join(d, f), root) for d, _, fs in os.walk(root) for f in fs)
        h.close()
        after = sorted(os.path.relpath(os.path.join(d, f), root) for d, _, fs in os.walk(root) for f in fs)
        T("installed power folder unchanged by tool use (no __pycache__, reports outside)", before == after and not any("__pycache__" in x for x in after), set(after) ^ set(before))
        out = os.path.join(h.home, "local-power")
        o = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "make_local_power.py"), out, "--python", "python3"], capture_output=True, text=True).stdout
        lp, errs = load_power(out)
        T("tools/make_local_power.py makes a valid power copy with the chosen Python command", lp is not None and not errs
          and json.load(open(os.path.join(out, "mcp.json")))["mcpServers"]["spindoctor-qwerty"]["command"] == "python3", (o, errs))
        o = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "make_local_power.py"), os.path.join(h.home, "w"), "--python", "py"], capture_output=True, text=True).stdout
        T("make_local_power.py --python py writes command py with args [-3, server] (Windows launcher)",
          json.load(open(os.path.join(h.home, "w", "mcp.json")))["mcpServers"]["spindoctor-qwerty"]["args"][0] == "-3", o)
        # shared end-to-end suite through the installed power's server, launched as the stand-in launches it
        e2e = os.path.join(HERE, "e2e_results.json"); cfg = p["servers"]["power-spindoctor-qwerty-spindoctor-qwerty"]
        argv = [shutil.which(cfg["command"])] + [expand(a, root, os.path.join(h.data, "spindoctor-qwerty")) for a in cfg["args"]]
        r = subprocess.run([sys.executable, os.path.join(HERE, "e2e_mcp.py"), "--server"] + argv + ["--examples", os.path.join(root, "skills", "spindoctor-qwerty", "examples", "theory"), "--out", e2e],
                           env=h.env, cwd=root, capture_output=True, text=True, timeout=3600)
        last = [l for l in r.stdout.splitlines() if l.strip()][-1:] or [""]
        T("shared end-to-end suite through the installed power's server: " + last[0][:60], r.returncode == 0, r.stdout[-400:])
    finally:
        h.close(); shutil.rmtree(h.home, ignore_errors=True)


def main():
    a = sys.argv[1:]; opt = dict(zip(a[::2], a[1::2]))
    static(); standin(opt.get("--source"))
    json.dump({"python": sys.version.split()[0], "host": "stand-in (Kiro Powers docs + Agent Plugins 1.0.0)", "checks": R},
              open(opt.get("--out", os.path.join(HERE, "host_check.json")), "w"), indent=1)
    n = sum(r["pass"] for r in R); print("%d/%d passed" % (n, len(R))); return 0 if n == len(R) else 1


if __name__ == "__main__":
    sys.exit(main())
