# NCAA Division I Women's Soccer Stats Scraper

This Python project scrapes Division I Women's Soccer team stats from the [NCAA website](https://www.ncaa.com/stats/soccer-women/d1) and compiles them into master CSV files for analysis.  

It’s designed to:  
- Automatically fetch all available team statistics.  
- Handle multiple pages per stat category.  
- Merge all stats into a single **master CSV** (`team_master.csv`).  
- Log stats that fail or contain only null values.  
- Be easily updated as NCAA updates stats.

> **Note:** Individual player stats scraping is currently commented out and will be added later. This version focuses on team stats only.

---

## Features

- Scrapes stats like:
  - Scoring Offense
  - Goals Against Average
  - Shots Per Game
  - Shutout Percentage
  - Win-Loss-Tied Percentage
  - Corner Kicks Per Game
  - Total Goals, Assists, Points, and more
- Handles stats with multiple pages automatically.
- Uses multithreading to speed up scraping.
- Generates a **master CSV** for immediate use in data analysis with pandas.
- Provides a scrape summary with:
  - Failed stats
  - Stats that are entirely null

---

