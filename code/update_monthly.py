import pandas as pd
import numpy as np
import json

month_idx = 1

mon_rank_path = "data/monthly_rank.csv"
mon_points_path = "data/monthly_points.csv"
current_month_path = "data/mensile.csv"
teams_path = "data/teams.json"

mon_rank_df = pd.read_csv(mon_rank_path)
mon_points_df = pd.read_csv(mon_points_path)
current_month_df = pd.read_csv(current_month_path)

with open(teams_path, "r", encoding="utf-8") as f:
    teams_data = json.load(f)

# pick the correct month column
month = mon_points_df.columns[month_idx]

for team in teams_data["teams"]:
    name = team["name"]

    # find indices
    idx_current = current_month_df.index[current_month_df["Squadra"] == name]
    idx_rank = mon_rank_df.index[mon_rank_df["Squadra"] == name]
    idx_points = mon_points_df.index[mon_points_df["Squadra"] == name]

    # skip team if not found everywhere
    if len(idx_current) == 0 or len(idx_rank) == 0 or len(idx_points) == 0:
        continue

    i_cur = idx_current[0]
    i_rank = idx_rank[0]
    i_pts = idx_points[0]

    # --- update rank ---
    rnk = int(current_month_df.at[i_cur, "Rank"])
    mon_rank_df.at[i_rank, month] = rnk

    team["budget"] += 200000 - (rnk - 1) * 10000

    # --- update points ---
    pnt = int(current_month_df.at[i_cur, "Punti"])
    mon_points_df.at[i_pts, month] = pnt
    mon_points_df.at[i_pts, "Totale"] += pnt

## add saving of the files, index increase and automation.

print(current_month_df.head(15))
print(mon_rank_df.head(15))
print(mon_points_df.head(15))