import json
import pandas as pd

# Paths to your files
json_file = "data/teams.json"
csv_file = "data/cqranking_riders.csv"
quarto_file = "c_squadre.md"
ranking_html_file = "classifica_totale.html"

# Load teams JSON
with open(json_file, "r", encoding="utf-8") as f:
    teams_data = json.load(f)

# Load riders CSV
df = pd.read_csv(csv_file)
df['Rider'] = df['Rider'].str.strip()  # Strip whitespace from Rider names

# Compute total points for each team
teams_points = []
for team in teams_data["teams"]:
    total_points = 0
    riders_info = []
    for rider_name in team["riders"]:
        rider_row = df[df["Rider"] == rider_name]
        if not rider_row.empty:
            rider_row = rider_row.iloc[0]
            cq = rider_row.get("CQ", 0)
            try:
                cq = float(cq)
            except:
                cq = 0
            flag_html = f'<img src="{rider_row["Country Flag"]}" width="20">' if "Country Flag" in rider_row and pd.notna(rider_row["Country Flag"]) else ""
        else:
            cq = 0
            flag_html = ""
        total_points += cq
        riders_info.append((flag_html, rider_name, int(cq)))
    teams_points.append({
        "name": team["name"],
        "total_points": int(total_points),
        "riders_info": riders_info
    })

# --- Part 1: Save overall ranking in HTML with small font and medals ---
teams_sorted_by_points = sorted(teams_points, key=lambda x: x["total_points"], reverse=True)

medals = ["🥇", "🥈", "🥉", "🪵"]

html_content = """
<div style="text-align:center; font-weight:bold; font-size:1.2em; margin-bottom: 2px;">
CLASSIFICA
</div>
<div style="font-size: small;">
<table style="border-collapse: collapse; width:100%;">
<thead>
<tr style="border-bottom:1px solid #ccc;">
<th style="text-align:center; padding:4px;"> </th>
<th style="text-align:left; padding:4px;"> </th>
<th style="text-align:right; padding:4px;"> Punti </th>
</tr>
</thead>
<tbody>
"""

for idx, team in enumerate(teams_sorted_by_points, start=1):
    medal = medals[idx - 1] if idx <= 4 else str(idx)
    html_content += (
        f"<tr>\n"
        f"<td style='text-align:center; padding:4px;'>{medal}</td>\n"
        f"<td style='text-align:left; padding:4px;'>{team['name']}</td>\n"
        f"<td style='text-align:right; padding:4px;'>{team['total_points']}</td>\n"
        f"</tr>\n"
    )

html_content += "</tbody>\n</table>\n</div>"

with open(ranking_html_file, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"HTML ranking with small font saved to {ranking_html_file}")

# --- Part 2: Save teams and riders to Quarto file alphabetically (no medals, no rank) ---
teams_sorted_alpha = sorted(teams_points, key=lambda x: x["name"].lower())

quarto_content = ""

for team in teams_sorted_alpha:
    # Team header with total points
    quarto_content += f"### {team['name']} <span style='float:right'>{team['total_points']}</span>\n\n"

    # Collapsible section for riders
    quarto_content += "<details>\n<summary>Corridori</summary>\n\n"
    quarto_content += '<table style="border-collapse: collapse; width:100%;">\n'
    quarto_content += '<thead>\n<tr>\n'
    headers = ["", "", "CQ pts"]
    widths = ["40px", "220px", "50px"]
    for h, w in zip(headers, widths):
        quarto_content += f'<th style="padding:4px;width:{w};text-align:center;">{h}</th>\n'
    quarto_content += '</tr>\n</thead>\n<tbody>\n'

    for flag_html, name, cq in team["riders_info"]:
        quarto_content += (
            f'<tr>\n'
            f'<td style="text-align:center;">{flag_html}</td>\n'
            f'<td style="text-align:left;">{name}</td>\n'
            f'<td style="text-align:center;">{cq}</td>\n'
            '</tr>\n'
        )

    quarto_content += '</tbody>\n</table>\n\n</details>\n\n'

# Write Quarto file
with open(quarto_file, "w", encoding="utf-8") as f:
    
    f.write(quarto_content)

print(f"Quarto file with team riders written to {quarto_file}")
