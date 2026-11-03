"""Run setup_and_run.py and publish its output as a static report in site/index.html.

    python build_site.py
"""
import html
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "site" / "index.html"
RULE = "=" * 70

CSS = """
:root{--bg:#070b14;--panel:#0e1524;--panel2:#121b2e;--fg:#e8eefc;--muted:#8a97b3;--line:#1f2b45;--accent:#38bdf8;--accent2:#34d399;--warn:#fbbf24}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:radial-gradient(1200px 500px at 70% -10%,#10264a55,transparent),var(--bg);color:var(--fg);font:16px/1.6 Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.top{position:sticky;top:0;z-index:10;backdrop-filter:blur(10px);background:#070b14cc;border-bottom:1px solid var(--line)}
.top div{max-width:1100px;margin:0 auto;padding:10px 20px;display:flex;gap:6px;align-items:center;flex-wrap:wrap}
.top b{margin-right:auto;font-size:14px;letter-spacing:.04em}
.top a{color:var(--muted);text-decoration:none;font-size:13px;padding:5px 12px;border-radius:999px}
.top a:hover{color:var(--fg);background:var(--panel2)}
main{max-width:1100px;margin:0 auto;padding:0 20px 90px}
.hero{padding:64px 0 28px}
.chip{display:inline-block;font-size:12px;color:var(--accent);border:1px solid #38bdf844;background:#38bdf812;border-radius:999px;padding:4px 12px;margin:0 6px 10px 0}
h1{font-size:clamp(30px,5vw,48px);line-height:1.1;margin:6px 0 10px;letter-spacing:-.02em}
.lead{color:var(--muted);max-width:720px;margin:0}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:30px 0 0}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px 18px}
.kpi b{display:block;font-size:30px;letter-spacing:-.02em;color:var(--accent)}
.kpi:nth-child(3n+2) b{color:var(--accent2)}.kpi:nth-child(3n) b{color:var(--warn)}
.kpi span{font-size:12px;color:var(--muted)}
h2{font-size:24px;margin:64px 0 6px;letter-spacing:-.01em}
h2 small{display:block;font-size:12px;color:var(--accent);letter-spacing:.14em;text-transform:uppercase;margin-bottom:4px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:18px 20px;margin:16px 0}
.card h3{margin:0 0 12px;font-size:15px;display:flex;gap:10px;align-items:center}
.card h3 i{font-style:normal;font-size:11px;background:#38bdf81c;color:var(--accent);border-radius:6px;padding:2px 8px;white-space:nowrap}
.card p.note{color:var(--muted);font-size:13px;margin:0 0 10px}
.scroll{overflow:auto;max-height:420px;border:1px solid var(--line);border-radius:10px}
table{border-collapse:collapse;width:100%;font-size:13px}
th{position:sticky;top:0;background:var(--panel2);text-align:left;color:var(--muted);font-weight:600;font-size:11px;letter-spacing:.06em;text-transform:uppercase;padding:9px 12px;white-space:nowrap}
td{padding:8px 12px;border-top:1px solid var(--line);vertical-align:middle}
td.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
tr:hover td{background:#16223a55}
.bar{display:block;height:6px;border-radius:3px;background:linear-gradient(90deg,var(--accent),var(--accent2));min-width:2px}
.stat{display:inline-flex;align-items:baseline;gap:10px;background:var(--panel2);border:1px solid var(--line);border-radius:12px;padding:10px 16px;margin:0 8px 8px 0}
.stat b{font-size:28px;color:var(--accent2)}.stat span{font-size:12px;color:var(--muted)}
.gauges{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
.gauge{background:var(--panel2);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.gauge b{font-size:30px}.gauge .track{height:8px;background:#1a2640;border-radius:4px;margin:10px 0 6px;overflow:hidden}
.gauge .track i{display:block;height:100%;background:linear-gradient(90deg,var(--accent),var(--accent2))}
.gauge span{font-size:12px;color:var(--muted)}
.more{font-size:12px;color:var(--muted);margin-top:8px}
pre{background:#050810;border:1px solid var(--line);border-radius:12px;padding:14px 16px;overflow:auto;max-height:560px;font:12.5px/1.5 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;margin:0;color:#c8d4f0}
details{margin-top:28px;background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:14px 18px}
summary{cursor:pointer;font-weight:700}
footer{margin-top:60px;color:var(--muted);font-size:12px;border-top:1px solid var(--line);padding-top:18px}
"""


def run_script():
    result = subprocess.run([sys.executable, str(ROOT / "setup_and_run.py")],
                            capture_output=True, text=True, cwd=ROOT, check=True,
                            env={**__import__("os").environ, "HI671_TSV": "1"})
    return result.stdout


def split_header(output):
    """The banner is RULE / title / author line / RULE; return (title, author, rest)."""
    lines = output.splitlines()
    if len(lines) > 3 and lines[0] == RULE and lines[3] == RULE:
        return lines[1].strip(), lines[2].strip(), "\n".join(lines[4:])
    return "HI 671 Query 2", "", output


def parse(output):
    """Split the console output into [(part_title, [(step_title, block), ...]), ...]."""
    parts, title, steps, step, buf = [], None, [], None, []

    def flush_step():
        nonlocal step, buf
        text = "\n".join(buf).strip("\n")
        if step or text:
            steps.append((step, text))
        step, buf = None, []

    lines = output.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line == RULE and i + 2 < len(lines) and lines[i + 2] == RULE:
            flush_step()
            if title is not None or steps:
                parts.append((title, steps))
            title, steps = lines[i + 1].strip(), []
            i += 3
            continue
        m = re.match(r"^--- (.+?) ---$", line)
        if m:
            flush_step()
            step = m.group(1)
        else:
            buf.append(line)
        i += 1
    flush_step()
    parts.append((title, steps))
    return [(t, [s for s in st if s[0] or s[1]]) for t, st in parts if t or st]


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def segments(block):
    """Split a step block into ('text', str) and ('table', header, rows) pieces."""
    out, buf, lines, i = [], [], block.splitlines(), 0
    while i < len(lines):
        if lines[i] == "@@TABLE":
            if "".join(buf).strip():
                out.append(("text", "\n".join(buf).strip()))
            buf, i = [], i + 1
            tbl = []
            while i < len(lines) and lines[i] != "@@END":
                tbl.append(lines[i].split("\t"))
                i += 1
            out.append(("table", tbl[0], tbl[1:]))
        else:
            buf.append(lines[i])
        i += 1
    if "".join(buf).strip():
        out.append(("text", "\n".join(buf).strip()))
    return out


def fnum(v):
    try:
        return float(v)
    except ValueError:
        return None


def pretty(v):
    f = fnum(v)
    if f is None:
        return html.escape(v)
    if f == int(f) and "." not in v:
        return html.escape(v)
    return f"{f:,.2f}".rstrip("0").rstrip(".") if abs(f) < 1e5 else f"{f:,.0f}"


def head(c):
    return html.escape(c.replace("_", " "))


def table_html(header, rows, step):
    if len(header) == 1 and len(rows) == 1:
        return f'<div class="stat"><b>{html.escape(rows[0][0])}</b><span>{head(header[0])}</span></div>'
    if "prevalence by gender" in (step or "").lower():
        cards = []
        for r in rows:
            d = dict(zip(header, r))
            pct = float(d["Diabetes_Percentage"])
            label = {"M": "Men", "F": "Women"}.get(d["gender"], d["gender"])
            cards.append(f'<div class="gauge"><span>{label}</span><br><b>{pct:.1f}%</b>'
                         f'<div class="track"><i style="width:{pct:.0f}%"></i></div>'
                         f'<span>{d["Diabetes_Patients"]} of {d["Total_Patients"]} patients</span></div>')
        return f'<div class="gauges">{"".join(cards)}</div>'
    if "top 2 months" in (step or "").lower():
        cards = []
        for r in rows:
            d = dict(zip(header, r))
            cards.append(f'<div class="gauge"><span>{html.escape(d["Month_Name"])}</span><br><b>{d["Total_Diagnoses"]}</b>'
                         f'<br><span>diagnoses reported</span></div>')
        return f'<div class="gauges">{"".join(cards)}</div>'
    bar_col = None
    if "average cost" in (step or "").lower():
        bar_col = header.index("Average_Cost")
        top = max(float(r[bar_col]) for r in rows)
    cap = 200 if len(rows) > 200 else None
    body = []
    for r in rows[:cap]:
        tds = []
        for j, v in enumerate(r):
            num = fnum(v) is not None and header[j] not in ("ICD", "icd9", "ICD9_Code", "icd", "ptid", "id", "claim_id")
            cell = pretty(v) if num else html.escape(v) or "&ndash;"
            if j == bar_col:
                cell = f'{pretty(v)}<span class="bar" style="width:{100*float(v)/top:.0f}%"></span>'
            dated = bool(__import__("re").fullmatch(r"\d{4}-\d{2}-\d{2}|[A-Z]{2}\d{5}|[A-Z]?\d{3}\.?\d*", v))
            tds.append(f'<td class="{"n" if num else ""}"{" style=white-space:nowrap" if dated else ""}>{cell}</td>')
        body.append("<tr>" + "".join(tds) + "</tr>")
    more = f'<div class="more">Showing the first {cap} of {len(rows)} rows.</div>' if cap else ""
    return (f'<div class="scroll"><table><thead><tr>{"".join(f"<th>{head(c)}</th>" for c in header)}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>{more}')


def first_cell(parts, needle):
    for _, steps in parts:
        for step, block in steps:
            if step and needle in step:
                for seg in segments(block):
                    if seg[0] == "table":
                        return seg[2][0][0], seg
    return None, None


def render(title_text, author, body_parts, sql):
    body_parts = [(t, s) for t, s in body_parts if t and not t.upper().startswith("ALL QUERIES")]
    kp = [("Patients after exclusion", first_cell(body_parts, "Remaining patients")[0]),
          ("Hyperlipidemia excluded", first_cell(body_parts, "Patients with Hyperlipidemia")[0]),
          ("Diabetes patients", first_cell(body_parts, "Count of Diabetes")[0])]
    _, err = first_cell(body_parts, "ICD codes with multiple")
    if err:
        kp.append(("Planted ICD errors found", str(len(err[2]))))
    _, mo = first_cell(body_parts, "Top 2 months")
    if mo:
        kp.append(("Peak month", mo[2][0][1]))
    kpis = "".join(f'<div class="kpi"><b>{html.escape(str(v))}</b><span>{k}</span></div>' for k, v in kp if v)
    nav = "".join(f'<a href="#{slug(t)}">{html.escape(t.split(":")[0].title())}</a>' for t, _ in body_parts)
    sections = []
    for pi, (title, steps) in enumerate(body_parts, 1):
        name = title.split(":", 1)[1].strip() if ":" in title else title
        sections.append(f'<h2 id="{slug(title)}"><small>Part {pi}</small>{html.escape(name)}</h2>')
        for step, block in steps:
            label = (step or "").split(":", 1)
            chip = html.escape(label[0].split(",", 1)[-1].strip()) if step else ""
            text = html.escape(label[1].strip() if len(label) > 1 else (step or ""))
            inner = ""
            for seg in segments(block):
                if seg[0] == "text":
                    inner += f'<p class="note">{html.escape(seg[1])}</p>'
                else:
                    inner += table_html(seg[1], seg[2], step)
            sections.append(f'<div class="card"><h3><i>{chip}</i>{text}</h3>{inner}</div>')
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>HI 671 Query 2 Results</title>
<meta name="description" content="Healthcare claims analysis in SQL: ICD9 to CCS mapping, diabetes cohort, cost, gender and data quality checks.">
<style>{CSS}</style></head>
<body>
<div class="top"><div><b>HI 671 &middot; Query 2</b>{nav}<a href="#sql">SQL</a>
<a href="https://github.com/rutvij1407/hi-671">GitHub</a></div></div>
<main>
<section class="hero">
<span class="chip">Health informatics</span><span class="chip">SQL</span><span class="chip">Synthetic data</span>
<h1>Healthcare claims analysis</h1>
<p class="lead">Grouping ICD9 diagnosis codes into clinical categories, then measuring cost, patient mix and data quality. By Rutvij Reddy Vakati, March 2026. Results come from running <code>setup_and_run.py</code> on a seeded synthetic dataset in DuckDB, so no real patient data is shown.</p>
<div class="kpis">{kpis}</div>
</section>
{"".join(sections)}
<details id="sql"><summary>Original SQL Server solution (HI671_Query2.sql)</summary><pre>{html.escape(sql)}</pre></details>
<footer>HI 671 course assignment, George Mason University. Rebuild with <code>python3 build_site.py</code>.</footer>
</main></body></html>
"""


def main():
    title_text, author, rest = split_header(run_script())
    parts = parse(rest)
    sql = (ROOT / "HI671_Query2.sql").read_text()
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(render(title_text, author, parts, sql))
    print(f"wrote {OUT.relative_to(ROOT)} ({len(parts)} parts, {sum(len(s) for _, s in parts)} steps)")


if __name__ == "__main__":
    main()
