import requests
import pandas as pd
from bs4 import BeautifulSoup
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# ----------------------------
# 1. TEAM STAT DICTIONARIES
# ----------------------------
# Fill in the IDs from the NCAA site dropdown
team_stats = {
    "Scoring Offense": 56,
    "Goals Against Average": 58,
    "Shots Per Game": 984,
    "Shutout Percentage": 59,
    "Save Percentage": 424,
    "Points Per Game": 95,
    "Assists Per Game": 94,
    "Win-Loss-Tied Percentage": 60,
    "Fouls Per Game": 547,
    "Corner Kicks Per Game": 1176,
    "Yellow Cards": 549,
    "Goal Differential": 1263,
    "Penalty Kicks": 1208,
    "Red Cards": 551,
    "Saves per Game": 93,
    "Shot Accuracy": 1203,
    "Shots on Goal Per Game": 986,
    "Total Assists": 910,
    "Total Goals": 914,
    "Total Points": 915
}

# ----------------------------
# 2. SCRAPER FUNCTION FOR TEAM STATS ONLY
# ----------------------------
def scrape_team_stat(stat_name, stat_id, session):
    """
    Scrapes a single team stat table from NCAA, handles multiple pages.
    Returns a DataFrame or None if failed.
    """
    base_url = f"https://www.ncaa.com/stats/soccer-women/d1/current/team/{stat_id}"
    all_data = []
    headers_row = None
    page = 1

    while True:
        # Add /p2, /p3, etc. for pagination
        url = base_url if page == 1 else f"{base_url}/p{page}"
        resp = session.get(url)
        if resp.status_code != 200:
            break  # stop if page does not exist

        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table")
        if not table:
            break  # stop if no table found

        rows = table.find_all("tr")
        if len(rows) <= 1:  # no data rows
            break

        # extract headers only once
        if headers_row is None:
            headers_row = [th.text.strip() for th in rows[0].find_all("th")]

        # extract row data
        for row in rows[1:]:
            cols = [td.text.strip() for td in row.find_all("td")]
            if cols:
                all_data.append(cols)

        page += 1  # move to next page

    if not all_data:
        return None  # nothing found

    df = pd.DataFrame(all_data, columns=headers_row)

    # For team stats, keep Team + last metric column
    entity_col = "Team"
    if entity_col not in df.columns:
        return None
    metric_col = df.columns[-1]
    df = df[[entity_col, metric_col]]
    df.rename(columns={metric_col: stat_name}, inplace=True)

    # check for all-null stat column
    if df[stat_name].isnull().all() or all(val.strip() == "" for val in df[stat_name]):
        return "NULL", df

    return df

# ----------------------------
# 3. BUILD MASTER TEAM CSV
# ----------------------------
def build_team_master(stat_dict):
    master_df = None
    total = len(stat_dict)
    done = 0
    failed_stats = []
    null_stats = []

    with requests.Session() as session:
        session.headers.update({"User-Agent": "Mozilla/5.0"})

        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {
                executor.submit(scrape_team_stat, stat_name, stat_id, session): stat_name
                for stat_name, stat_id in stat_dict.items()
            }

            for future in as_completed(futures):
                stat_name = futures[future]
                try:
                    result = future.result()

                    if result is None:
                        failed_stats.append(stat_name)
                    elif isinstance(result, tuple) and result[0] == "NULL":
                        null_stats.append(stat_name)
                        df = result[1]
                        if master_df is None:
                            master_df = df
                        else:
                            master_df = pd.merge(master_df, df, on="Team", how="outer")
                    else:
                        df = result
                        if master_df is None:
                            master_df = df
                        else:
                            master_df = pd.merge(master_df, df, on="Team", how="outer")

                except Exception as e:
                    failed_stats.append(f"{stat_name} (error: {e})")

                done += 1
                print(f"[{done}/{total}] Processed team stat: {stat_name}")

    return master_df, failed_stats, null_stats

# ----------------------------
# 4. RUN TEAM SCRAPER
# ----------------------------
os.makedirs("ncaa_stats", exist_ok=True)

print("Scraping team stats...")
team_master, team_failed, team_null = build_team_master(team_stats)
if team_master is not None:
    team_master.to_csv("ncaa_stats/team_master.csv", index=False)
    print("✅ team_master.csv saved")

# ----------------------------
# 5. ERROR SUMMARY
# ----------------------------
print("\n---- SCRAPE SUMMARY ----")
if team_failed:
    print(f"❌ Team stats failed: {team_failed}")
if team_null:
    print(f"⚠️ Team stats with all nulls: {team_null}")

# ----------------------------
# Individual stats section commented out for now
# ----------------------------
# # print("\nScraping individual stats...")
# # indiv_master, indiv_failed, indiv_null = build_master(individual_stats, "individual")
# # if indiv_master is not None:
# #     indiv_master.to_csv("ncaa_stats/individual_master.csv", index=False)
# #     print("✅ individual_master.csv saved")
