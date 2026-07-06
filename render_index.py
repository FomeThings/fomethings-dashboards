#!/usr/bin/env python3
"""FomeThings — generate the dashboards portfolio index from umbrellas.yaml.

Reads each umbrella's canonical STATE.yaml (in its project repo) and renders a
polished index.html grouped by project, with a status chip + progress bar per
umbrella. Derived, not duplicated: the STATE.yaml is the source of truth.

Usage:  python3 render_index.py        # run from the fomethings-dashboards repo
Output: index.html (overwritten).
Stack-agnostic (Python only). Uses PyYAML if available, else a minimal fallback.
"""
from __future__ import annotations
import html
import sys
from pathlib import Path

STATUS = {  # derived umbrella status -> (label, color)
    "completa": ("Completa", "#16a34a"),
    "activa": ("Activa", "#2563eb"),
    "bloqueada": ("Bloqueada", "#dc2626"),
}


def load_yaml(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text) or {}
    except ImportError:
        return _mini(text)


def _scalar(v: str):
    v = v.strip()
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        return [x.strip().strip('"').strip("'") for x in inner.split(",")] if inner else []
    return v.strip('"').strip("'")


def _mini(text: str) -> dict:
    """Top-level scalars + `phases`/`umbrellas` list (each item = flat key:vals,
    phases may hold nested `steps`). Matches the constrained schemas here."""
    data: dict = {}
    lst_key = None
    lst: list = []
    cur: dict | None = None
    cur_indent = -1
    for raw in text.split("\n"):
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        line = raw.split(" #", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        s = line.strip()
        if indent == 0 and s.endswith(":") and s.rstrip(":") in ("phases", "umbrellas"):
            if lst_key:
                data[lst_key] = lst
            lst_key, lst, cur = s.rstrip(":"), [], None
            continue
        if indent == 0 and ":" in s and not s.startswith("-"):
            if lst_key:
                data[lst_key] = lst
                lst_key, lst = None, []
            k, v = s.split(":", 1)
            data[k.strip()] = _scalar(v)
            continue
        if lst_key is None:
            continue
        if s.startswith("- "):
            cur = {}
            cur_indent = indent
            lst.append(cur)
            item = s[2:]
            if ":" in item:
                k, v = item.split(":", 1)
                cur[k.strip()] = _scalar(v)
        elif cur is not None and ":" in s and indent > cur_indent:
            k, v = s.split(":", 1)
            cur[k.strip()] = _scalar(v)
    if lst_key:
        data[lst_key] = lst
    return data


def tally(phases: list[dict]) -> tuple[int, int]:
    done = total = 0
    for p in phases:
        steps = p.get("steps") or []
        if steps:
            total += len(steps)
            done += sum(1 for s in steps if str(s.get("status")) == "done")
        else:
            total += 1
            done += 1 if str(p.get("status")) == "done" else 0
    return done, total


def derive_status(state: dict, pct: int) -> str:
    phases = state.get("phases") or []
    if any(str(p.get("status")) == "blocked" for p in phases):
        return "bloqueada"
    return "completa" if pct >= 100 else "activa"


def esc(x) -> str:
    return html.escape(str(x if x is not None else ""))


def card(u: dict, state: dict) -> str:
    phases = state.get("phases") or []
    done, total = tally(phases)
    pct = round(done / total * 100) if total else 0
    st = derive_status(state, pct)
    label, color = STATUS[st]
    phase = esc(state.get("current_phase") or "")
    updated = esc(state.get("last_updated") or "")
    return f"""
  <a class="card" href="./{esc(u.get('slug'))}/">
    <div class="top">
      <h3>{esc(u.get('title') or state.get('title'))}</h3>
      <span class="chip" style="color:{color};background:{color}1a;border-color:{color}66"><i style="background:{color}"></i>{label}</span>
    </div>
    <div class="track"><i style="width:{pct}%"></i></div>
    <div class="cap"><span class="tnum">{done}/{total} fases · {pct}%</span><span>Fase: <b>{phase}</b></span></div>
    <div class="upd tnum">Actualizado {updated}</div>
  </a>"""


def render(manifest: dict, root: Path) -> str:
    umbrellas = manifest.get("umbrellas") or []
    # group by project, preserving first-seen order
    groups: dict[str, list] = {}
    for u in umbrellas:
        sp = (root / str(u.get("state"))).resolve()
        if not sp.exists():
            print(f"  ! STATE not found for {u.get('slug')}: {sp}", file=sys.stderr)
            continue
        state = load_yaml(sp)
        groups.setdefault(str(u.get("project") or "Sin proyecto"), []).append((u, state))
    sections = []
    for project, items in groups.items():
        cards = "".join(card(u, st) for u, st in items)
        sections.append(f'<section><p class="grp">{esc(project)}</p>{cards}</section>')
    return TEMPLATE.replace("{{SECTIONS}}", "".join(sections))


TEMPLATE = """<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FomeThings — Dashboards</title><style>
:root{--bg:#f6f8fb;--surf:#fff;--surf2:#f1f5f9;--bd:#e2e8f0;--fg:#0f172a;--mut:#64748b;--fnt:#94a3b8;--a:#3b82f6;--a2:#22c55e}
@media(prefers-color-scheme:dark){:root{--bg:#0a0e17;--surf:#111826;--surf2:#0e1420;--bd:#1e293b;--fg:#e6edf6;--mut:#93a2b8;--fnt:#64748b;--a:#60a5fa;--a2:#4ade80}}
*{box-sizing:border-box}body{margin:0;font:15px/1.55 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--fg);padding:40px 18px;-webkit-font-smoothing:antialiased}
.wrap{max-width:680px;margin:0 auto}
.eyebrow{font-size:11px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--a);margin:0 0 8px}
h1{font-size:clamp(22px,4vw,28px);font-weight:700;letter-spacing:-.02em;margin:0 0 6px}
.sub{color:var(--mut);margin:0 0 28px;font-size:14px}
.grp{font-size:10.5px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--fnt);margin:26px 0 10px}
section:first-of-type .grp{margin-top:0}
.tnum{font-variant-numeric:tabular-nums}
a.card{display:block;background:var(--surf);border:1px solid var(--bd);border-radius:13px;padding:15px 17px;text-decoration:none;color:inherit;margin-bottom:12px;box-shadow:0 1px 2px rgba(15,23,42,.05),0 8px 22px rgba(15,23,42,.04);transition:border-color .15s}
a.card:hover{border-color:var(--a)}
.top{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:11px}
.top h3{margin:0;font-size:16px;font-weight:650;letter-spacing:-.01em}
.chip{display:inline-flex;align-items:center;gap:6px;font-size:11.5px;font-weight:600;padding:3px 9px;border-radius:999px;border:1px solid;white-space:nowrap}
.chip i{width:6px;height:6px;border-radius:50%}
.track{height:7px;background:var(--surf2);border:1px solid var(--bd);border-radius:999px;overflow:hidden}
.track>i{display:block;height:100%;background:linear-gradient(90deg,var(--a),var(--a2))}
.cap{display:flex;justify-content:space-between;gap:12px;margin:8px 0 2px;font-size:12.5px;color:var(--mut)}.cap b{color:var(--fg)}
.upd{font-size:11.5px;color:var(--fnt)}
.foot{margin-top:26px;font-size:12px;color:var(--fnt);text-align:center}
</style></head><body><div class="wrap">
<p class="eyebrow">FomeThings · Umbrella Mission Control</p>
<h1>Umbrella Dashboards</h1>
<p class="sub">Iniciativas multi-fase, agrupadas por proyecto. Estado y progreso derivados del STATE.yaml de cada umbrella (se embeben en sus páginas de Notion).</p>
{{SECTIONS}}
<p class="foot">Generado desde umbrellas.yaml + los STATE.yaml por render_index.py — no editar a mano.</p>
</div></body></html>"""


def main() -> int:
    root = Path(__file__).resolve().parent
    manifest = load_yaml(root / "umbrellas.yaml")
    (root / "index.html").write_text(render(manifest, root), encoding="utf-8")
    n = len(manifest.get("umbrellas") or [])
    print(f"wrote index.html ({n} umbrella(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
