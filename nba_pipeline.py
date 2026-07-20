# Finding the NBA library and grabbing the game logs for the 2024-25 season
from nba_api.stats.endpoints import playergamelogs
import pandas as pd
import time

print("Pulling NBA game logs...")

# Storing the game logs for the 2024-25 season in a dataframe
logs = playergamelogs.PlayerGameLogs(season_nullable='2024-25')

# Waiting 1 second so the API doesn't get overwhelmed with requests
time.sleep(1)

# Getting the dataframe from logs
df = logs.get_data_frames()[0]

# Displaying the total number of rows, columns, and the first 3 rows of the dataframe

# Keeping only the important columns 
cols = ['PLAYER_NAME', 'TEAM_ABBREVIATION', 'GAME_DATE',
        'PTS', 'REB', 'AST', 'STL', 'BLK',
        'FG_PCT', 'FG3_PCT', 'FT_PCT', 'MIN', 'PLUS_MINUS', 'WL']

df = df[cols]


# Rename columns to  lowercase names
df.columns = ['player', 'team', 'date', 'points', 'rebounds',
              'assists', 'steals', 'blocks', 'fg_pct',
              'fg3_pct', 'ft_pct', 'minutes', 'plus_minus', 'win_loss']

# Drops any rows with missing values
df = df.dropna()

# Convert date column from a string to an actual date
df['date'] = pd.to_datetime(df['date'])

# Convert the minutes column to a float
df['minutes'] = df['minutes'].astype(float)

# Create a new column (points per minute)
df['points_per_minute'] = (df['points'] / df['minutes']).round(3)



# Save cleaned data to a CSV file
df.to_csv('cleaned_nba_stats.csv', index=False)

print("Cleaned data saved to cleaned_nba_stats.csv")

import sqlite3

# Connect to the SQLite database 
conn = sqlite3.connect('nba.db')
df.to_sql('game_logs', conn, if_exists='replace', index=False)

# Querying the database for top scorers 
print("\n Top 10 scorers in the 2024-25 season:")
q1 = pd.read_sql_query('''
SELECT player, team, ROUND(AVG(points), 2) AS avg_points, COUNT(*) AS games
FROM game_logs
GROUP BY player, team
HAVING games >= 30
ORDER BY avg_points DESC
LIMIT 10
''', conn)

print(q1)

# Querying the database for most efficient scorers (points per minute)
print("\n Top 10 most efficient scorers (points per minute) in the 2024-25 season:")

q2 = pd.read_sql_query('''
SELECT player, team, ROUND(AVG(points_per_minute), 3) AS avg_points_per_minute, COUNT(*) AS games       
FROM game_logs
GROUP BY player, team
HAVING COUNT(*) >= 40
ORDER BY avg_points_per_minute DESC
LIMIT 10
''', conn)

print(q2)

# Querying the database for top scorers that shoot over 50 percent from the field
print("\n Top Scorers that shoot over 50 percent from the field in the 2024-25 season:")

q3 = pd.read_sql_query('''
SELECT player, team, ROUND(AVG(points), 2) AS avg_points, ROUND(AVG(fg_pct), 3) AS avg_fg_pct, COUNT(*) AS games
FROM game_logs
GROUP BY player, team
HAVING COUNT(*) >= 40 and avg_points >= 20
ORDER BY avg_fg_pct DESC
LIMIT 10
''', conn)

print(q3)

# Querying the database for most dominant defensive players (steals + blocks)
print("\n Top 10 most dominant defensive players (steals + blocks) in the 2024-25 season:")

q4 = pd.read_sql_query('''
SELECT player, team, ROUND(AVG(steals), 2) AS avg_steals, ROUND(AVG(blocks), 2) AS avg_blocks, COUNT(*) AS games
FROM game_logs
GROUP BY player, team
HAVING COUNT(*) >= 40
ORDER BY (avg_steals + avg_blocks) DESC
LIMIT 10
''', conn)

print(q4)

conn.close()


import matplotlib.pyplot as plt
import seaborn as sns

# Reconnect to the SQLite database to create charts
conn = sqlite3.connect('nba.db')

# Chart 1 (Top 10 scorers in the 2024-25 season)

scorers = pd.read_sql_query('''
SELECT player, team, ROUND(AVG(points), 2) AS avg_points
FROM game_logs
GROUP BY player, team
ORDER BY avg_points DESC
LIMIT 10
''', conn)

plt.figure(figsize=(12, 6))
sns.barplot(data=q1, x='avg_points', y='player', color='steelblue')
plt.title('Top 10 Scorers in the 2024-25 NBA Season')
plt.xlabel('PPG (Points Per Game)')
plt.ylabel('Player')
plt.tight_layout()
plt.savefig('Chart 1: Top 10 Scorers.png')
plt.close()

# CHART 2  most efficient scorers (points per minute)
q2 = pd.read_sql("""
    SELECT player, ROUND(AVG(points_per_minute), 3) as avg_ppm
    FROM game_logs
    GROUP BY player
    HAVING COUNT(*) >= 40
    ORDER BY avg_ppm DESC
    LIMIT 10
""", conn)

plt.figure(figsize=(12, 6))
sns.barplot(data=q2, x='avg_ppm', y='player', color='darkorange')
plt.title('Top 10 Most Efficient Scorers (Points Per Minute) - 2024-25 Season', fontsize=14)
plt.xlabel('Points Per Minute')
plt.ylabel('Player')
plt.tight_layout()
plt.savefig('chart2_efficiency.png')
plt.close()

# CHART 3  Top Scorers that shoot over 50 percent from the field
q3 = pd.read_sql("""
    SELECT player, ROUND(AVG(points), 2) as avg_points, ROUND(AVG(fg_pct), 3) as avg_fg_pct
    FROM game_logs
    GROUP BY player
    HAVING COUNT(*) >= 40 AND AVG(points) >= 20
    ORDER BY avg_fg_pct DESC
    LIMIT 10
""", conn)      

plt.figure(figsize=(12, 6))
sns.barplot(data=q3, x='avg_fg_pct', y='player', color='green')
for i, row in q3.iterrows():
    plt.annotate(row['player'], (row['avg_fg_pct'], row['avg_points']),
                 textcoords="offset points", xytext=(5, 5), fontsize=8)
plt.title('Top Scorers Shooting 50%+ From the Field - 2024-25 Season', fontsize=14)
plt.xlabel('Field Goal Percentage')
plt.ylabel('Points Per Game')
plt.tight_layout()
plt.savefig('chart3_fg_pct.png')
plt.close()

# Chart 4  most dominant defensive players (steals + blocks)
q4 = pd.read_sql("""
    SELECT player, ROUND(AVG(steals), 2) as avg_steals, ROUND(AVG(blocks), 2) as avg_blocks
    FROM game_logs
    GROUP BY player
    HAVING COUNT(*) >= 40
    ORDER BY (avg_steals + avg_blocks) DESC
    LIMIT 10
""", conn)

plt.figure(figsize=(12, 6))
q4_melted = q4.melt(id_vars='player', value_vars=['avg_steals', 'avg_blocks'],
var_name='stat', value_name='value')
sns.barplot(data=q4_melted, x='value', y='player', hue='stat',
palette={'avg_steals': 'blue', 'avg_blocks': 'crimson'})
plt.title('Top 10 Defensive Players (Steals + Blocks) - 2024-25 Season', fontsize=14)
plt.xlabel('Average Per Game')
plt.ylabel('Player')
plt.legend(title='Stat', labels=['Steals', 'Blocks'])
plt.tight_layout()
plt.savefig('chart4_defense.png')
plt.close()

conn.close()
print("\nAll 4 charts saved successfully.")