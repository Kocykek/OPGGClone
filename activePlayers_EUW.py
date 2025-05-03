import requests
import mysql.connector
import datetime
from requests.exceptions import ChunkedEncodingError, RequestException, JSONDecodeError
import time

API_KEY = "insert api key here"

tiers_with_divisions = ["DIAMOND","EMERALD","PLATINUM","GOLD","SILVER","BRONZE","IRON"]
tiers_without_divisions = ["MASTER","GRANDMASTER","CHALLENGER"]
divisions = ["I","II","III","IV"]
regions = ["EUW1"]


headers = {
    "X-Riot-Token": API_KEY
}

db_config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'newpassword',
    'database': 'leaguestats'
}

conn = mysql.connector.connect(**db_config) # Using config to connect to database
cursor = conn.cursor()

cursor.execute("SELECT puuid FROM summoners")
existingPlayers = set(row[0] for row in cursor.fetchall())


for region in regions:
    for tier in tiers_with_divisions:
        print(tier)
        for division in divisions:
            counter = 1
            while True:
                url = f"https://{region.lower()}.api.riotgames.com/lol/league/v4/entries/RANKED_SOLO_5x5/{tier}/{division}?page={counter}&" # fetch matches url with divisions
                
                for atttempt in range(3):
                    try:
                        players = requests.get(url, headers=headers, timeout=20)
                        if players.status_code == 429:
                        # If rate-limited, wait for the time specified in the `Retry-After` header
                            retry_after = int(players.headers.get('Retry-After', 60))  # Default to 60 seconds if not specified
                            print(f"Rate limited. Retrying after {retry_after} seconds...")
                            time.sleep(retry_after)
                            continue
                        data = players.json()
                        break # go out and go further into fetching
                    except ChunkedEncodingError as e:
                        print(f"ChunkedEncodingError on attempt {e}")
                        time.sleep(2)  # wait a bit before retrying
                    except RequestException as e:
                        print(f"Request failed: {e}")
                        break  # other request-related error, don't retry
                    except Exception as e:
                        print(f"Unexpected error: {e}")
                        break
                else:
                    print("Failed to get data.")
                    continue #skip to next division / tier
                
                if not data:
                    break
                
                if region != "KR":
                    short_region = region[:-1]  # for example "EUN1" -> "EUN" so it works with database's table's name :)
                else:
                    short_region = "KR"

                if short_region == "EUN" or short_region == "EUW":
                    puuidPart = "europe"
                elif short_region == "NA":
                    puuidPart = "americas"
                elif short_region == "KR":
                    puuidPart = "asia"
                
                cursor.execute("SELECT regionId FROM regions WHERE name = %s", (short_region,)) # Getting region's ID based on server - EUN,EUW,NA,KR
                regionId_result = cursor.fetchone()
                
                if not regionId_result:
                    raise Exception("Region not found :c")
                
                regionId = regionId_result[0]
                cursor.execute("""
                    SELECT idDivisionTier FROM whatdivisiontier 
                    WHERE Division = %s AND Tier = %s
                """, (division, tier))
                dt_result = cursor.fetchone()
                print(f"DEBUG: division='{division}', tier='{tier}'")

                if not dt_result:
                    raise Exception(f"DivisionTier not found for division='{division}' and tier='{tier}'")
                whatdivisiontierId = dt_result[0]
                print(data)
                for player in data:
                    print(player)
                    wins = player['wins']
                    losses = player['losses']
                    overall = wins + losses
                    if overall>600:
                        puuid = player['puuid']
                        summonerId = player['summonerId']
                        leaguePoints = player['leaguePoints']
                        timeNow = datetime.datetime.utcnow()
                        puuidUrl = f"https://{puuidPart}.api.riotgames.com/riot/account/v1/accounts/by-puuid/{puuid}"
                        puuidFetch = requests.get(puuidUrl, headers=headers, timeout=20)
                        if puuidFetch.status_code == 429:
                        # If rate-limited, wait for the time specified in the `Retry-After` header
                            retry_after = int(puuidFetch.headers.get('Retry-After', 60))  # Default to 60 seconds if not specified
                            print(f"Rate limited. Retrying after {retry_after} seconds...")
                            time.sleep(retry_after)
                            continue
                        dataFromPuuid = puuidFetch.json()
                        if 'gameName' not in dataFromPuuid or 'tagLine' not in dataFromPuuid:
                            print(f"Missing gameName or tagLine for PUUID: {puuid}")
                            print("Response:", dataFromPuuid)
                            continue  # Skip this player
                        gameName = dataFromPuuid['gameName']
                        tagLine = dataFromPuuid['tagLine']
                        nameTag = gameName+"#"+tagLine
                        summonerUrl = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/{summonerId}"
                        summonerFetch = requests.get(summonerUrl, headers=headers, timeout=20)
                        if summonerFetch.status_code == 200:
                            try:
                                dataFromSummoner = summonerFetch.json()
                            except requests.exceptions.JSONDecodeError:
                                print("Failed to decode JSON from response.")
                                print("Response content:", summonerFetch.text)
                                dataFromSummoner = None
                        else:
                            print(f"Error fetching summoner data: {summonerFetch.status_code}")
                            print("Response content:", summonerFetch.text)
                            dataFromSummoner = None
                        summonerIcon = dataFromSummoner['profileIconId']
                        summonerLevel = dataFromSummoner['summonerLevel']
                        if puuid in existingPlayers:
                            time_str = timeNow.strftime('%Y-%m-%d %H:%M:%S')
                            nameTag_sql = nameTag.replace("'", "\\'")
                            update_sql_line = f"""UPDATE summoners
                            SET leaguePoints = {leaguePoints},
                                wins = {wins}, 
                                losses = {losses}, 
                                whatdivisiontierId = {whatdivisiontierId}, 
                                nameTag = '{nameTag_sql}', 
                                summonerIcon = {summonerIcon}, 
                                lastUpdated = '{time_str}', 
                                summonerLevel = {summonerLevel},
                                regionId = {regionId}
                            WHERE puuid = '{puuid}';\n"""

                            with open("update_commands_EUW.sql", "a", encoding="utf-8") as f:
                                f.write(update_sql_line)
                        else:
                            time_str = timeNow.strftime('%Y-%m-%d %H:%M:%S')
                            nameTag_sql = nameTag.replace("'", "\\'")
                            sql_line = f"""INSERT INTO summoners (
                                summonerId, puuid, leaguePoints, wins, losses,
                                whatdivisiontierId, nameTag, summonerIcon, lastUpdated, summonerLevel, regionId
                                ) VALUES (
                                '{summonerId}', '{puuid}', {leaguePoints}, {wins}, {losses},
                                {whatdivisiontierId}, '{nameTag_sql}', {summonerIcon}, '{time_str}', {summonerLevel}, {regionId}
                            );\n"""

                            with open("insert_commands_EUW.sql", "a", encoding="utf-8") as f:
                                f.write(sql_line)

                counter += 1
            conn.commit()
            

cursor.close()
conn.close()
