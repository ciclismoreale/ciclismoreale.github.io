import json
import pandas as pd

# =========================
# Paths
# =========================
json_file = "data/teams.json"
csv_file = "data/cqranking_riders.csv"
csv_file_pre = "data/cqranking_riders_preseason.csv"
csv_monthly = "data/monthly_points.csv"

quarto_file = "c_squadre.md"

ranking_html_file_big = "classifica_totale_big.html"
ranking_html_file_small = "classifica_totale_small.html"
ranking_html_file_monthly = "classifica_mensile.html"

ranking_csv_total = "data/totale.csv"
ranking_csv_monthly = "data/mensile.csv"

# =========================
# Load data
# =========================
with open(json_file, "r", encoding="utf-8") as f:
    teams_data = json.load(f)

df = pd.read_csv(csv_file)
df_pre = pd.read_csv(csv_file_pre)
df_monthly = pd.read_csv(csv_monthly)

df["Rider"] = df["Rider"].astype(str).str.strip()
df_pre["Rider"] = df_pre["Rider"].astype(str).str.strip()

df_monthly["team"] = df_monthly["Squadra"].astype(str).str.strip()

# Pre-season lookup
preseason_points = (
    df_pre.set_index("Rider")["CQ"]
    .fillna(0)
    .astype(float)
    .to_dict()
)

# Monthly lookup (points BEFORE this month)
monthly_base_points = (
    df_monthly.set_index("team")["Totale"]
    .fillna(0)
    .astype(float)
    .to_dict()
)

# =========================
# Compute team points
# =========================
teams_points = []

for team in teams_data["teams"]:
    total_points = 0
    riders_info = []

    for rider_name in team["riders"]:
        rider_row = df[df["Rider"] == rider_name]

        if not rider_row.empty:
            rider_row = rider_row.iloc[0]
            cq = pd.to_numeric(rider_row.get("CQ", 0), errors="coerce") or 0
            flag_html = (
                f'<img src="{rider_row["Country Flag"]}" width="20">'
                if "Country Flag" in rider_row and pd.notna(rider_row["Country Flag"])
                else ""
            )
        else:
            cq = 0
            flag_html = ""

        cq_pre = pd.to_numeric(preseason_points.get(rider_name, 0), errors="coerce") or 0
        net_cq = cq - cq_pre

        total_points += net_cq

        riders_info.append([
            flag_html,
            rider_name,
            int(cq),
            int(cq_pre),
            int(net_cq)
        ])
    # add pre-season riders
    preseason = ""
    for rider, points in team["preseason"].items():
        total_points += points
        preseason += f"{rider} ({points}) "

    
    # Sort riders by net points descending
    riders_info.sort(key=lambda x: x[4], reverse=True)

    base_monthly = monthly_base_points.get(team["name"], 0)
    monthly_points = total_points - base_monthly

    teams_points.append({
        "name": team["name"],
        "total_points": int(total_points),
        "monthly_points": int(monthly_points),
        "riders_info": riders_info,
        "budget": team["budget"],
        "preseason": preseason
    })

# =========================
# HTML builders
# =========================
medals = ["🥇", "🥈", "🥉", "🪵"]

def build_html_ranking(teams_sorted, title=None, small=False):
    parts = []

    if title:
        parts.append(
            f'<div style="text-align:center;font-weight:bold;font-size:1.2em;margin-bottom:4px;">'
            f'{title}</div>'
        )

    parts.append('<div style="font-size:small;">' if small else '<div>')
    parts.append('<table style="border-collapse:collapse;width:100%;">')
    parts.append(
        '<thead>'
        '<tr style="border-bottom:1px solid #ccc;">'
        '<th style="text-align:center;padding:4px;"></th>'
        '<th style="text-align:left;padding:4px;"></th>'
        '<th style="text-align:right;padding:4px;">CQ pts</th>'
        '</tr>'
        '</thead><tbody>'
    )

    for idx, team in enumerate(teams_sorted, start=1):
        medal = medals[idx - 1] if idx <= 4 else str(idx)
        parts.append(
            '<tr>'
            f'<td style="text-align:center;padding:4px;">{medal}</td>'
            f'<td style="text-align:left;padding:4px;">{team["name"]}</td>'
            f'<td style="text-align:right;padding:4px;">{team["points"]}</td>'
            '</tr>'
        )

    parts.append('</tbody></table></div>')
    return "".join(parts)

# =========================
# TOTAL ranking
# =========================
total_sorted = sorted(
    teams_points, key=lambda x: x["total_points"], reverse=True
)

total_html_big = build_html_ranking(
    [{"name": t["name"], "points": t["total_points"]} for t in total_sorted]
)

total_html_small = build_html_ranking(
    [{"name": t["name"], "points": t["total_points"]} for t in total_sorted],
    title="CLASSIFICA",
    small=True
)

with open(ranking_html_file_big, "w", encoding="utf-8") as f:
    f.write(total_html_big)

with open(ranking_html_file_small, "w", encoding="utf-8") as f:
    f.write(total_html_small)

# =========================
# MONTHLY ranking
# =========================
monthly_sorted = sorted(
    teams_points, key=lambda x: x["monthly_points"], reverse=True
)

monthly_html = build_html_ranking(
    [{"name": t["name"], "points": t["monthly_points"]} for t in monthly_sorted],
)

with open(ranking_html_file_monthly, "w", encoding="utf-8") as f:
    f.write(monthly_html)

# =========================
# CSV outputs
# =========================
pd.DataFrame([
    {"Rank": i + 1, "Squadra": t["name"], "Punti": t["total_points"]}
    for i, t in enumerate(total_sorted)
]).to_csv(ranking_csv_total, index=False)

pd.DataFrame([
    {"Rank": i + 1, "Squadra": t["name"], "Punti": t["monthly_points"]}
    for i, t in enumerate(monthly_sorted)
]).to_csv(ranking_csv_monthly, index=False)

# =========================
# Quarto output (unchanged)
# =========================
teams_sorted_alpha = sorted(teams_points, key=lambda x: x["name"].lower())
quarto_content = ""

for team in teams_sorted_alpha:
    quarto_content += (
        f"### {team['name']} "
        f"<span style='float:right'> CQ pts: {team['total_points']}</span>\n\n"
    )
    quarto_content += f"**Budget:** {team['budget']:,}".replace(",", " ") + " $\n"

    quarto_content += "<details>\n<summary>Corridori</summary>\n"
    quarto_content += '<table style="border-collapse:collapse;width:100%;">\n'
    quarto_content += '<thead><tr>\n'

    headers = ["", "", "CQ", "Pre-asta", "Netti"]
    widths = ["40px", "220px", "50px", "80px", "50px"]

    for h, w in zip(headers, widths):
        quarto_content += f'<th style="width:{w};text-align:center;">{h}</th>\n'

    quarto_content += '</tr></thead>\n<tbody>\n'

    for flag_html, name, cq, cq_pre, net in team["riders_info"]:
        quarto_content += (
            '<tr>'
            f'<td style="text-align:center;">{flag_html}</td>'
            f'<td style="text-align:left;">{name}</td>'
            f'<td style="text-align:center;">{cq}</td>'
            f'<td style="text-align:center;">{cq_pre}</td>'
            f'<td style="text-align:center;">{net}</td>'
            '</tr>\n'
        )
    quarto_content += '</tbody></table>\n'
    if team["preseason"] != "":
        quarto_content += "**Pre-asta: **"
        quarto_content += team["preseason"]
        quarto_content += '\n'
    quarto_content += '</details>\n'

with open(quarto_file, "w", encoding="utf-8") as f:
    f.write(quarto_content)

print("Total & monthly rankings (HTML + CSV) generated successfully.")