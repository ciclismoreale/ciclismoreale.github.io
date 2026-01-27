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

    html = f"""<style>
.table-container {{
  width: 100%;
  overflow-x: auto;
}}

.fixed-table {{
  border-collapse: collapse;
  table-layout: fixed;
  min-width: 1000px;
  font-size: 12px;
}}

.fixed-table th,
.fixed-table td {{
  border: 1px solid #ccc;
  padding: 4px 8px;
  white-space: nowrap;
  text-align: center;
}}

.fixed-table th {{
  background: #f4f4f4;
  position: sticky;
  top: 0;
  z-index: 2;
  font-weight: 600;
}}

.fixed-table .fixed-col {{
  position: sticky;
  left: 0;
  background: white;
  font-weight: 600;
  text-align: left;
  min-width: 150px;
  z-index: 3;
}}

.fixed-table .month-col {{
  width: 90px;
  min-width: 90px;
  max-width: 90px;
}}
</style>

<div class="table-container">
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
