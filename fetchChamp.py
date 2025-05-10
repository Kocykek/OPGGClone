import requests
import mysql.connector

# Fetch data from Riot's Data Dragon
url = "https://ddragon.leagueoflegends.com/cdn/15.9.1/data/en_US/champion.json"
response = requests.get(url)
champ_data = response.json()["data"]

# MySQL connection config
db_config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'newpassword',
    'database': 'leaguestats'
}

conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# Prepare SQL insert query
insert_query = """
    INSERT INTO champions (champKey, name)
    VALUES (%s, %s)
"""

# Insert each champion
for champ_name, champ_info in champ_data.items():
    champ_key = int(champ_info["key"])
    name = champ_info["name"]
    cursor.execute(insert_query, (champ_key, name))

conn.commit()
cursor.close()
conn.close()

print("Champions inserted successfully.")
