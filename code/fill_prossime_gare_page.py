"""
Build c_prossime_gare.md: for each fantasy team, the upcoming races of
its riders (scraped from ProCyclingStats by scrape_pcs_program.py).

Table styling lives in styles.css under .program-table.
"""

from datetime import datetime

import pandas as pd

PROGRAM_CSV = "data/pcs_program.csv"
RIDERS_CSV = "data/cqranking_riders.csv"
OUTPUT_FILE = "c_prossime_gare.md"


def format_date(iso_date):
    """'2026-08-22' -> '22/08'. Falls back to the raw string if it
    doesn't parse (defensive -- PCS's date format is out of our
    control)."""
    try:
        return datetime.strptime(iso_date, "%Y-%m-%d").strftime("%d/%m")
    except (ValueError, TypeError):
        return iso_date or ""


def load_flags():
    try:
        df = pd.read_csv(RIDERS_CSV)
    except FileNotFoundError:
        return {}
    df["Rider"] = df["Rider"].astype(str).str.strip()
    return dict(zip(df["Rider"], df.get("Country Flag", "")))


def main():
    try:
        program_df = pd.read_csv(PROGRAM_CSV)
    except FileNotFoundError:
        program_df = pd.DataFrame(columns=["Team", "Rider", "Date", "Race", "Class", "RaceURL"])

    flags = load_flags()

    content = []
    teams = sorted(program_df["Team"].unique(), key=str.lower) if not program_df.empty else []

    # Make sure every team gets a section even if none of its riders
    # had a parsable program, by pulling the full team list from
    # teams.json rather than only teams present in the CSV.
    import json

    with open("data/teams.json", "r", encoding="utf-8") as f:
        teams_data = json.load(f)
    all_team_names = sorted((t["name"] for t in teams_data["teams"]), key=str.lower)

    for team_name in all_team_names:
        content.append(f"### {team_name}\n\n")

        team_rows = (
            program_df[program_df["Team"] == team_name].copy()
            if not program_df.empty
            else pd.DataFrame()
        )

        if team_rows.empty:
            content.append(
                '<p class="text-muted small">Nessuna gara in programma trovata per i corridori di questa squadra.</p>\n\n'
            )
            continue

        team_rows["_sort_date"] = pd.to_datetime(team_rows["Date"], errors="coerce")
        team_rows = team_rows.sort_values(["_sort_date", "Rider"])

        content.append('<div class="table-responsive">\n')
        content.append('<table class="table table-striped table-hover table-sm program-table">\n')
        content.append(
            "<thead><tr>"
            '<th class="col-flag"></th>'
            "<th>Corridore</th>"
            '<th class="text-center">Data</th>'
            "<th>Gara</th>"
            '<th class="text-center">Classe</th>'
            "</tr></thead>\n<tbody>\n"
        )

        for _, row in team_rows.iterrows():
            rider = row["Rider"]
            flag_url = flags.get(rider, "")
            flag_html = f'<img class="flag" src="{flag_url}" width="20">' if pd.notna(flag_url) and flag_url else ""
            date_str = format_date(row["Date"])
            race_name = row["Race"]
            race_url = row["RaceURL"]
            race_html = f'<a href="{race_url}" target="_blank">{race_name}</a>' if pd.notna(race_url) and race_url else race_name
            race_class = row["Class"] if pd.notna(row["Class"]) else ""

            content.append(
                "<tr>"
                f'<td class="text-center">{flag_html}</td>'
                f"<td>{rider}</td>"
                f'<td class="text-center">{date_str}</td>'
                f"<td>{race_html}</td>"
                f'<td class="text-center">{race_class}</td>'
                "</tr>\n"
            )

        content.append("</tbody></table>\n</div>\n\n")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("".join(content))


if __name__ == "__main__":
    main()
