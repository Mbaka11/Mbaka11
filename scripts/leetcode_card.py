"""Generate assets/leetcode.svg (light + dark) from the LeetCode GraphQL API."""
import json, sys, urllib.request, datetime as dt

USER = "mBaka"
Q = """query($u:String!){matchedUser(username:$u){submitStats{acSubmissionNum{difficulty count}}
userCalendar{streak totalActiveDays submissionCalendar}}}"""

def fetch():
    req = urllib.request.Request(
        "https://leetcode.com/graphql",
        json.dumps({"query": Q, "variables": {"u": USER}}).encode(),
        {"Content-Type": "application/json", "Referer": "https://leetcode.com", "User-Agent": "mbaka11-profile-readme"})
    return json.load(urllib.request.urlopen(req))["data"]["matchedUser"]

def build(d):
    solved = {x["difficulty"]: x["count"] for x in d["submitStats"]["acSubmissionNum"]}
    cal = d["userCalendar"]
    days = sorted((int(k), v) for k, v in json.loads(cal["submissionCalendar"]).items())
    cum, tot = [], 0
    for t, v in days:
        tot += v; cum.append((t, tot))
    W, H = 760, 260
    x0, x1, y0, y1 = 330, 730, 70, 200
    tmin, tmax = cum[0][0], cum[-1][0]
    span = max(tmax - tmin, 1)
    pts = [(x0 + (t - tmin) / span * (x1 - x0), y1 - c / tot * (y1 - y0)) for t, c in cum]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"{x0},{y1} " + line + f" {x1},{y1}"
    fmt = lambda t: dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%b %d")
    bars, y = "", 95
    total = max(solved["All"], 1)
    for name, col in (("Easy", "#00b8a3"), ("Medium", "#ffb800"), ("Hard", "#ef4743")):
        n = solved[name]
        bars += (f'<text x="30" y="{y+10}" class="m">{name}</text>'
                 f'<rect x="100" y="{y}" width="150" height="10" rx="5" class="trk"/>'
                 f'<rect x="100" y="{y}" width="{max(150*n/total,4):.0f}" height="10" rx="5" fill="{col}"/>'
                 f'<text x="262" y="{y+10}" class="v">{n}</text>')
        y += 32
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">
<style>
:root{{--bg:#fff;--fg:#1f2328;--mut:#656d76;--trk:#e6e8eb;--acc:#ffa116;--bd:#d0d7de}}
@media (prefers-color-scheme:dark){{:root{{--bg:#0d1117;--fg:#e6edf3;--mut:#8b949e;--trk:#21262d;--acc:#ffa116;--bd:#30363d}}}}
.t{{font-size:16px;font-weight:600;fill:var(--fg)}} .m{{font-size:12px;fill:var(--mut)}}
.v{{font-size:12px;font-weight:600;fill:var(--fg)}} .big{{font-size:34px;font-weight:700;fill:var(--fg)}}
.trk{{fill:var(--trk)}} .ln{{stroke:var(--acc);stroke-width:2.5;fill:none;stroke-linejoin:round}}
.ar{{fill:var(--acc);opacity:.15}} .gr{{stroke:var(--bd);stroke-width:1}}
</style>
<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="10" fill="var(--bg)" stroke="var(--bd)"/>
<text x="30" y="38" class="t">LeetCode · {USER}</text>
{bars}
<text x="30" y="205" class="big">{solved["All"]}</text><text x="30" y="224" class="m">problems solved</text>
<text x="150" y="205" class="big">{cal["streak"]}</text><text x="150" y="224" class="m">day streak</text>
<text x="240" y="205" class="big">{cal["totalActiveDays"]}</text><text x="240" y="224" class="m">active days</text>
<text x="{x0}" y="38" class="m">Cumulative submissions · past year</text>
<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" class="gr"/><line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y0}" class="gr" stroke-dasharray="3 4"/>
<polygon points="{area}" class="ar"/><polyline points="{line}" class="ln"/>
<circle cx="{pts[-1][0]:.1f}" cy="{pts[-1][1]:.1f}" r="4" fill="var(--acc)"/>
<text x="{x0}" y="{y1+18}" class="m">{fmt(tmin)}</text><text x="{x1}" y="{y1+18}" class="m" text-anchor="end">{fmt(tmax)}</text>
<text x="{x1}" y="{y0-8}" class="v" text-anchor="end">{tot}</text>
</svg>'''

if __name__ == "__main__":
    open("assets/leetcode.svg", "w", encoding="utf-8").write(build(fetch()))
