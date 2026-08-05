"""
Build c_prossime_gare.md: for each fantasy team, the upcoming races of
its riders (scraped from ProCyclingStats by scrape_pcs_program.py),
grouped by race so each row is one race with the list of that team's
riders taking part.

Table styling lives in styles.css under .program-table.
"""

import json
from datetime import datetime

import pandas as pd

PROGRAM_CSV = "data/pcs_program.csv"
NO_PROGRAM_CSV = "data/pcs_no_program.csv"
RIDERS_CSV = "data/cqranking_riders.csv"
TEAMS_JSON = "data/teams.json"
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


def rider_badge(rider_name, flags):
    flag_url = flags.get(rider_name, "")
    flag_html = (
        f'<img class="flag" src="{flag_url}" width="16">'
        if isinstance(flag_url, str) and flag_url
        else ""
    )
    return f'<span class="program-rider">{flag_html}{rider_name}</span>'


def main():
    try:
        program_df = pd.read_csv(PROGRAM_CSV)
    except FileNotFoundError:
        program_df = pd.DataFrame(columns=["Team", "Rider", "Date", "Race", "Class", "RaceURL"])

    try:
        no_program_df = pd.read_csv(NO_PROGRAM_CSV)
    except FileNotFoundError:
        no_program_df = pd.DataFrame(columns=["Team", "Rider"])

    flags = load_flags()

    with open(TEAMS_JSON, "r", encoding="utf-8") as f:
        teams_data = json.load(f)
    all_team_names = sorted((t["name"] for t in teams_data["teams"]), key=str.lower)

    content = []

    for team_name in all_team_names:
        content.append(f"### {team_name}\n\n")

        team_rows = (
            program_df[program_df["Team"] == team_name].copy()
            if not program_df.empty
            else pd.DataFrame()
        )
        team_no_program = (
            sorted(no_program_df[no_program_df["Team"] == team_name]["Rider"].tolist())
            if not no_program_df.empty
            else []
        )

        if team_rows.empty and not team_no_program:
            content.append(
                '<p class="text-muted small">Nessuna gara in programma trovata per i corridori di questa squadra.</p>\n\n'
            )
            continue

        if not team_rows.empty:
            # One row per race: group all riders on this team who have
            # that race in their program together.
            grouped = (
                team_rows.groupby(["Date", "Race", "Class", "RaceURL"], dropna=False)["Rider"]
                .apply(list)
                .reset_index()
            )
            grouped["_sort_date"] = pd.to_datetime(grouped["Date"], errors="coerce")
            grouped = grouped.sort_values(["_sort_date", "Race"])

            content.append('<div class="table-responsive">\n')
            content.append('<table class="table table-striped table-hover table-sm program-table">\n')
            content.append(
                "<thead><tr>"
                '<th class="col-date text-center">Data</th>'
                '<th class="col-race">Gara</th>'
                '<th class="col-class text-center">Classe</th>'
                '<th class="col-riders">Corridori</th>'
                "</tr></thead>\n<tbody>\n"
            )

            for _, row in grouped.iterrows():
                date_str = format_date(row["Date"])
                race_name = row["Race"]
                race_url = row["RaceURL"]
                race_html = (
                    f'<a href="{race_url}" target="_blank">{race_name}</a>'
                    if pd.notna(race_url) and race_url
                    else race_name
                )
                race_class = row["Class"] if pd.notna(row["Class"]) else ""
                riders_html = " ".join(
                    rider_badge(r, flags) for r in sorted(row["Rider"])
                )

                content.append(
                    "<tr>"
                    f'<td class="col-date text-center">{date_str}</td>'
                    f'<td class="col-race">{race_html}</td>'
                    f'<td class="col-class text-center">{race_class}</td>'
                    f'<td class="col-riders">{riders_html}</td>'
                    "</tr>\n"
                )

            content.append("</tbody></table>\n</div>\n\n")

        if team_no_program:
            names = ", ".join(team_no_program)
            content.append(
                f'<p class="text-muted small">Nessuna gara in programma per: {names}.</p>\n\n'
            )

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("".join(content))


if __name__ == "__main__":
    main()
