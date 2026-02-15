import pandas as pd
import numpy as np
import json
import os

# ------------------
# paths
# ------------------
mon_rank_path = "data/monthly_rank.csv"
mon_points_path = "data/monthly_points.csv"
current_month_path = "data/mensile.csv"
teams_path = "data/teams.json"
state_path = "data/state.json"   # <-- persistent state for monthly numbering

# load persistent state
if os.path.exists(state_path):
    with open(state_path, "r", encoding="utf-8") as f:
        state = json.load(f)
    month_idx = state.get("month_idx", 1)
else:
    month_idx = 1
    state = {}

# load data
mon_rank_df = pd.read_csv(mon_rank_path)
mon_points_df = pd.read_csv(mon_points_path)
current_month_df = pd.read_csv(current_month_path)

with open(teams_path, "r", encoding="utf-8") as f:
    teams_data = json.load(f)

# month column
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

    # update rank
    rnk = int(current_month_df.at[i_cur, "Rank"])
    mon_rank_df.at[i_rank, month] = rnk
    team["budget"] += 200000 - (rnk - 1) * 10000

    # update points
    pnt = int(current_month_df.at[i_cur, "Punti"])
    mon_points_df.at[i_pts, month] = pnt
    mon_points_df.at[i_pts, "Totale"] += pnt

mon_rank_df.to_csv(mon_rank_path, index=False)
mon_points_df.to_csv(mon_points_path, index=False)

with open(teams_path, "w", encoding="utf-8") as f:
    json.dump(teams_data, f, indent=4, ensure_ascii=False)

# INCREMENT MONTH + SAVE STATE
state["month_idx"] = month_idx + 1

with open(state_path, "w", encoding="utf-8") as f:
    json.dump(state, f, indent=4)
