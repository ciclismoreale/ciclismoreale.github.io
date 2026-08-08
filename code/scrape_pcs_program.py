"""
Scrape each fantasy team's riders' upcoming race program from
ProCyclingStats and save it to data/pcs_program.csv.

Riders whose ProCyclingStats page can't be found under any of our
best-guess slugs (name mismatches between CQranking and
ProCyclingStats) are skipped -- see pcs_common.name_to_slug_candidates
for the matching approach.
"""

import json
import time

import requests

from pcs_common import name_to_slug_candidates, fetch_program, SLEEP_BETWEEN_REQUESTS

TEAMS_JSON = "data/teams.json"
OUTPUT_CSV = "data/pcs_program.csv"
NO_PROGRAM_CSV = "data/pcs_no_program.csv"


def main():
    with open(TEAMS_JSON, "r", encoding="utf-8") as f:
        teams_data = json.load(f)

    session = requests.Session()

    # Cache by rider name so a rider drafted on more than one team (or
    # listed twice by mistake) is only fetched once.
    program_cache = {}
    unmatched = []
    rows = []
    # Riders who *do* have a matching PCS page but currently have no
    # upcoming races listed -- distinct from riders we couldn't match
    # at all, and worth surfacing on the page rather than silently
    # dropping (see fill_prossime_gare_page.py).
    no_program_rows = []

    for team in teams_data.get("teams", []):
        team_name = team.get("name", "-")
        for rider_name in team.get("riders", []):
            if rider_name not in program_cache:
                candidates = name_to_slug_candidates(rider_name)
                program = None
                matched_slug = None
                tried = []

                for slug in candidates:
                    tried.append(slug)
                    try:
                        program = fetch_program(session, slug)
                    except requests.RequestException as exc:
                        print(f"  ! request failed for {rider_name} ({slug}): {exc}")
                        program = None
                    time.sleep(SLEEP_BETWEEN_REQUESTS)

                    if program is not None:
                        matched_slug = slug
                        break

                program_cache[rider_name] = program

                if program is None:
                    unmatched.append(rider_name)
                    tried_str = ", ".join(f"'{s}'" for s in tried) if tried else "(no candidate slugs)"
                    print(f"  no PCS match: {rider_name} (tried {tried_str})")
                else:
                    print(f"  {rider_name}: {len(program)} upcoming race(s) (slug '{matched_slug}')")

            program = program_cache[rider_name]
            if program is None:
                continue

            if not program:
                no_program_rows.append({"Team": team_name, "Rider": rider_name})
                continue

            for race in program:
                rows.append(
                    {
                        "Team": team_name,
                        "Rider": rider_name,
                        "Date": race["date"],
                        "Race": race["race"],
                        "Class": race["class"],
                        "RaceURL": race["url"],
                    }
                )

    import pandas as pd

    df = pd.DataFrame(rows, columns=["Team", "Rider", "Date", "Race", "Class", "RaceURL"])
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

    no_program_df = pd.DataFrame(no_program_rows, columns=["Team", "Rider"])
    no_program_df.to_csv(NO_PROGRAM_CSV, index=False, encoding="utf-8")

    print(
        f"Done. {len(program_cache) - len(unmatched)} riders matched "
        f"({len(no_program_rows)} with no upcoming races), "
        f"{len(unmatched)} skipped (no PCS match), {len(rows)} upcoming race rows saved."
    )


if __name__ == "__main__":
    main()
