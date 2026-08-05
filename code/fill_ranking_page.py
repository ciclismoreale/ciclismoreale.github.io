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
# Table styling (zebra stripes, hover, sticky header, pagination
# button look) lives in styles.css under .cq-ranking-table / .cq-pagination.
with open(output_file, "w", encoding="utf-8") as f:
    # ---- Table ----
    f.write('<div class="table-responsive">\n')
    f.write('<table class="table table-striped table-hover table-sm cq-ranking-table">\n')
    f.write('<thead>\n<tr>\n')

    headers = [
        ("Rank", "col-rank"),
        ("", "col-flag"),
        ("Rider", "col-rider"),
        ("Squadra", ""),
        ("Fantasquadra", ""),
        ("CQ pts", ""),
    ]

    for h, cls in headers:
        cls_attr = f' class="{cls}"' if cls else ""
        f.write(f'<th{cls_attr}>{h}</th>\n')

    f.write('</tr>\n</thead>\n<tbody>\n')

    # ---- Table rows ----
    for i, row in df.iterrows():
        page = i // ROWS_PER_PAGE

        flag = (
            f'<img class="flag" src="{row["Country Flag"]}" width="20">'
            if pd.notna(row["Country Flag"])
            else ""
        )
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
            f'<tr class="page page-{page}">\n'
            f'<td class="text-center">{row["Rank"]}</td>\n'
            f'<td class="text-center">{flag}</td>\n'
            f'<td>{rider}</td>\n'
            f'<td class="text-center">{dob}</td>\n'
            f'<td class="text-center">{true_team}</td>\n'
            f'<td class="text-center">{fanta_team}</td>\n'
            f'<td class="text-center">{cq_pts}</td>\n'
            '</tr>\n'
        )

    f.write('</tbody>\n</table>\n</div>\n')

    # ---- Pagination buttons ----
    f.write('<div id="pagination" class="cq-pagination">\n')

    for i in range(num_pages):
        f.write(
            f'<button class="btn btn-outline-secondary btn-sm" '
            f'onclick="showPage({i})">{i + 1}</button>\n'
        )

    f.write('</div>\n')

    # ---- JavaScript pagination ----
    # Rows start hidden via the .cq-ranking-table tbody tr.page CSS rule
    # (styles.css) rather than a per-row inline style, so the table never
    # flashes fully expanded before this script runs.
    f.write("""
<script>
function showPage(page) {
    document.querySelectorAll('.page').forEach(row => {
        row.style.display = 'none';
    });
    document.querySelectorAll('.page-' + page).forEach(row => {
        row.style.display = '';
    });

    document.querySelectorAll('#pagination button').forEach((b, i) => {
        b.classList.toggle('active', i === page);
    });
}
showPage(0);
</script>
""")

