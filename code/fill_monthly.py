import pandas as pd

def scrollable_table(csv_file, output_file):
    df = pd.read_csv(csv_file)

    # Build header
    thead = "<thead><tr>"
    for i, col in enumerate(df.columns):
        cls = "fixed-col" if i == 0 else "month-col"
        thead += f'<th class="{cls}">{col}</th>'
    thead += "</tr></thead>"

    # Build body
    tbody = "<tbody>"
    for _, row in df.iterrows():
        tbody += "<tr>"
        for i, val in enumerate(row):
            cls = "fixed-col" if i == 0 else "month-col"
            tbody += f'<td class="{cls}">{val}</td>'
        tbody += "</tr>"
    tbody += "</tbody>"

    # Styling for .table-container / .fixed-table lives in styles.css
    # (shared across monthly_points.md and monthly_rank.md).
    html = f"""<div class="table-container">
<table class="fixed-table">
{thead}
{tbody}
</table>
</div>
"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)


csv_file_points = "data/monthly_points.csv"
output_file_points = "monthly_points.md"
scrollable_table(csv_file_points, output_file_points)

csv_file_rank = "data/monthly_rank.csv"
output_file_rank = "monthly_rank.md"
scrollable_table(csv_file_rank, output_file_rank)
