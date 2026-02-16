import pandas as pd
import math
import json

# ----------------- FILE PATHS -----------------
csv_file = "data/cqranking_riders.csv"
teams_json = "data/teams.json"
output_file = "c_cq_ranking.md"

# ----------------- READ CSV -----------------
df = pd.read_csv(csv_file)

# ----------------- LOAD TEAMS -----------------
with open(teams_json, "r", encoding="utf-8") as jf:
    teams_data = json.load(jf)

rider_to_fantateam = {}
for team in teams_data.get("teams", []):
    team_name = team.get("name", "-")
    for rider in team.get("riders", []):
        rider_to_fantateam[rider.upper()] = team_name

# ----------------- FANTASQUADRA -----------------
def get_fantateam(rider):
    if pd.isna(rider):
        return "-"
    return rider_to_fantateam.get(rider.upper(), "-")

df["Fantasquadra"] = df["Rider"].apply(get_fantateam)


# ----------------- PAGINATION -----------------
ROWS_PER_PAGE = 100
num_pages = math.ceil(len(df) / ROWS_PER_PAGE)

# ----------------- WRITE OUTPUT -----------------
with open(output_file, "w", encoding="utf-8") as f:
    # ---- Table ----
    f.write('<table style="border-collapse: collapse; width:100%;">\n')
    f.write('<thead>\n<tr>\n')

    headers = [
        "Rank",
        "",
        "",
        "",
        "Squadra",
        "Fantasquadra",
        "CQ pts",
    ]

    widths = [
        "30px",
        "30px",
        "200px",
        "90px",
        "80px",
        "180px",
        "60px",
    ]

    for h, w in zip(headers, widths):
        f.write(f'<th style="padding:4px;width:{w};text-align:center;">{h}</th>\n')

    f.write('</tr>\n</thead>\n<tbody>\n')

    # ---- Table rows ----
    for i, row in df.iterrows():
        page = i // ROWS_PER_PAGE

        flag = f'<img src="{row["Country Flag"]}" width="20">' if pd.notna(row["Country Flag"]) else ""
        rider = row["Rider"].replace("  ", "&nbsp;&nbsp;") if pd.notna(row["Rider"]) else ""
        dob = row["Date of birth"] if pd.notna(row["Date of birth"]) else ""
        true_team = row["Team"] if pd.notna(row["Team"]) else ""
        fanta_team = row["Fantasquadra"]
        try:
            cq_pts = int(row["CQ"])
        except:
            print(row)
            cq_pts = "-"

        f.write(
            f'<tr class="page page-{page}" style="display:none;">\n'
            f'<td style="text-align:center;">{row["Rank"]}</td>\n'
            f'<td style="text-align:center;">{flag}</td>\n'
            f'<td style="text-align:left;">{rider}</td>\n'
            f'<td style="text-align:center;">{dob}</td>\n'
            f'<td style="text-align:center;">{true_team}</td>\n'
            f'<td style="text-align:center;">{fanta_team}</td>\n'
            f'<td style="text-align:center;">{cq_pts}</td>\n'
            '</tr>\n'
        )

    f.write('</tbody>\n</table>\n')

    # ---- Pagination buttons ----
    f.write("""
<div id="pagination" style="margin-top:15px; text-align:center;">
""")

    for i in range(num_pages):
        f.write(
            f'<button onclick="showPage({i})" '
            f'style="margin:3px;padding:5px 10px;">{i+1}</button>\n'
        )

    f.write('</div>\n')

    # ---- JavaScript pagination ----
    f.write("""
<script>
function showPage(page) {
    document.querySelectorAll('.page').forEach(row => {
        row.style.display = 'none';
    });
    document.querySelectorAll('.page-' + page).forEach(row => {
        row.style.display = '';
    });

    document.querySelectorAll('#pagination button').forEach((b,i) => {
        b.style.fontWeight = (i === page) ? 'bold' : 'normal';
    });
}
showPage(0);
</script>
""")

