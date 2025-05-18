import requests
from datetime import datetime
import mysql.connector
# Riot API key
import time
API_KEY = "api key"

headers = {
    "X-Riot-Token": API_KEY
}

db_config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'newpassword',
    'database': 'leaguestats'
}

support_full_items = [3869, 3870, 3871, 3876, 3877]
support_item_replaced = False

region_map = {
    1: 'europe',   # EUN (eun1)
    2: 'europe',   # EUW (euw1)
    3: 'americas', # NA (na1)
    4: 'asia',     # KR (kr)
}

db = mysql.connector.connect(**db_config)

cursor = db.cursor(dictionary=True)
cursor.execute("SELECT puuid, whatdivisiontierId, regionId FROM summoners ORDER BY RAND() LIMIT 1")
user_data = cursor.fetchone()
# print(user_data)
puuid = user_data['puuid']
whatDivision = user_data['whatdivisiontierId']
region_id = user_data['regionId']

whatRegionUrl = region_map.get(region_id, 'europe')  # fallback to europe by default
# Match ID and endpoint


matchesUrl = f"https://{whatRegionUrl}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=100" 
responseMatches = requests.get(matchesUrl, headers=headers)

try:
    listOfMatches = responseMatches.json()
except ValueError as e:
    print("Failed to decode JSON:", e)
    listOfMatches = []
    exit()

for match in listOfMatches:
    print(match)


    onlyOneMatchID = match
    match_id = onlyOneMatchID
    url = f"https://{whatRegionUrl}.api.riotgames.com/lol/match/v5/matches/{match_id}"

    # Make the API request
    response = requests.get(url, headers=headers)
    if response.status_code == 429:
        print("Rate limit exceeded. Sleeping for 10 seconds...")
        time.sleep(60)
        continue
    elif response.status_code == 403:
        print("Forbidden – check if your API key is valid!")
        time.sleep(60)
        continue
    elif response.status_code != 200:
        print(f"Unexpected status code {response.status_code}. Skipping...")
        continue
    
    match_data = response.json()
    

    # Extract and process relevant match info
    match_name = match_id

    select_query = "SELECT 1 FROM matches WHERE matchName = %s LIMIT 1"
    cursor.execute(select_query, (match_name,))
    match_exists = cursor.fetchone()

    print(match_exists)
    # print(match_exists)

    select_query = "SELECT * FROM items WHERE isBoots = 1"
    cursor.execute(select_query)
    boots_items = cursor.fetchall()
    boots_item_ids = {item['itemId'] for item in boots_items}

    select_query = "SELECT itemId FROM items WHERE isFullItem = 1"
    cursor.execute(select_query)
    all_full_items = cursor.fetchall()
    all_full_item_ids = {item['itemId'] for item in all_full_items}

    select_query = "SELECT champKey, name from champions"
    cursor.execute(select_query)
    all_champions = cursor.fetchall()
    champion_name_to_key = {champ['name']: champ['champKey'] for champ in all_champions}
    # print(all_champions)



    if match_exists == None:
        timelineUrl = f"https://{whatRegionUrl}.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"
        responseTimeline = requests.get(timelineUrl, headers=headers)
        if responseTimeline.status_code == 200:
            try:
                timeline_data = responseTimeline.json()
            except ValueError as e:
                print(f"JSON decoding failed: {e}")
                timeline_data = None
                continue  # skip to next match
        else:
            print(f"Error fetching timeline for match {match_id}: {responseTimeline.status_code}")
            continue  # skip this match and go to next
        print(match_id)

        if "info" not in match_data:
            exit()

        match_type = match_data["info"]["queueId"]

        if match_type in [420,400,440]:
            game_creation_unix = match_data["info"]["gameCreation"] // 1000
            match_start = datetime.utcfromtimestamp(game_creation_unix).strftime('%Y-%m-%d %H:%M:%S')
            match_duration = match_data["info"]["gameDuration"]

            game_ended_early = match_data['info']['participants'][0]['gameEndedInEarlySurrender']
            if game_ended_early:
                game_ended_early = 1
            else:
                game_ended_early = 0

            match_win = match_data["info"]["participants"][0]["win"]
            if match_win:
                match_win = 1
            else:
                match_win = 0

            bans = []
            for team in match_data['info']['teams']:
                for ban in team.get('bans', []):
                    bans.append(ban['championId'])
            print(bans)
            ban1 = bans[0]
            ban2 = bans[1]
            ban3 = bans[2]
            ban4 = bans[3]
            ban5 = bans[4]
            ban6 = bans[5]
            ban7 = bans[6]
            ban8 = bans[7]
            ban9 = bans[8]
            ban10 = bans[9]
    # Print out match info
        # print("Match Info:")
        # print(f"Match Name   : {match_name}")
        # print(f"Match Type   : {match_type}")
        # print(f"Match Start  : {match_start}")
        # print(f"Duration     : {match_duration} seconds")
        # print(bans)
        # print(game_ended_early)
        # print("Did team 1 win?", match_win)

            insert_query = """
                INSERT INTO matches (matchName, matchType, matchStart, matchDuration, isRemake, ban1, ban2, ban3, ban4, ban5, ban6, ban7, ban8, ban9, ban10, win, whatDivisionTier )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query,(match_name, match_type, match_start, match_duration,game_ended_early, ban1, ban2, ban3, ban4, ban5, ban6, ban7, ban8, ban9, ban10, match_win, whatDivision))
            match_id = cursor.lastrowid
            db.commit()


            selectId_query = "SELECT matchId from matches WHERE matchName = %s LIMIT 1"
            cursor.execute(selectId_query, (match_name,))
            match_identificator = cursor.fetchone()
    # print("test")
    # print(match_identificator['matchId'])

    # FETCHING PARTICIPANTS INFO NOW! [matchInfo] table

            playerCounter = 0
            enemyCounter = 5
            team = 0


            firstItems =  timeline_data['info']['frames'][1]['events']
            framesOverall = timeline_data['info']['frames']

            for participant in match_data['metadata']['participants']:
                participantPuuid = participant

                cursor.execute("SELECT userId FROM summoners WHERE puuid = %s", (participantPuuid,))
                result = cursor.fetchone()
                cursor.fetchall()
                if result:
                    user_id = result["userId"]
                else:
                    cursor.execute("INSERT INTO summoners (puuid) VALUES (%s)", (participantPuuid,))
                    db.commit()
                    user_id = cursor.lastrowid



                participantTeam = team
        
                participantKills = match_data['info']['participants'][playerCounter]['kills']
                participantDeaths = match_data['info']['participants'][playerCounter]['deaths']
                participantAssists = match_data['info']['participants'][playerCounter]['assists']
                participantChampLevel = match_data['info']['participants'][playerCounter]['champLevel']
                participantChamp = match_data['info']['participants'][playerCounter]['championName']
            # participantChampKey = champion_name_to_key.get(participantChamp)
                participantChampKey = match_data['info']['participants'][playerCounter]['championId']
                participantRune1 = match_data['info']['participants'][playerCounter]['perks']['styles'][0]['selections'][0]['perk']
                participantRune2 = match_data['info']['participants'][playerCounter]['perks']['styles'][0]['selections'][1]['perk']
                participantRune3 = match_data['info']['participants'][playerCounter]['perks']['styles'][0]['selections'][2]['perk']
                participantRune4 = match_data['info']['participants'][playerCounter]['perks']['styles'][0]['selections'][3]['perk']

                participantSideRune5 = match_data['info']['participants'][playerCounter]['perks']['styles'][1]['selections'][0]['perk']
                participantSideRune6 = match_data['info']['participants'][playerCounter]['perks']['styles'][1]['selections'][1]['perk']

                participantCircleRune7 = match_data['info']['participants'][playerCounter]['perks']['statPerks']['offense']
                participantCircleRune8 = match_data['info']['participants'][playerCounter]['perks']['statPerks']['flex']
                participantCircleRune9 = match_data['info']['participants'][playerCounter]['perks']['statPerks']['defense']

                participantSpell1 = match_data['info']['participants'][playerCounter]['summoner1Id']
                participantSpell2 = match_data['info']['participants'][playerCounter]['summoner2Id']

                participantItem1 = match_data['info']['participants'][playerCounter]['item0']
                participantItem2 = match_data['info']['participants'][playerCounter]['item1']
                participantItem3 = match_data['info']['participants'][playerCounter]['item2']
                participantItem4 = match_data['info']['participants'][playerCounter]['item3']
                participantItem5 = match_data['info']['participants'][playerCounter]['item4']
                participantItem6 = match_data['info']['participants'][playerCounter]['item5']
                participantItem7 = match_data['info']['participants'][playerCounter]['item6']

                participantRole = match_data['info']['participants'][playerCounter]['lane']

                participantDamageDealt = match_data['info']['participants'][playerCounter]['totalDamageDealtToChampions']
                participantEnemyChamp = match_data['info']['participants'][enemyCounter]['championId']
                participantLargestMultiKill = match_data['info']['participants'][playerCounter]['largestMultiKill']
                participantMinionsKilled = match_data['info']['participants'][playerCounter]['totalMinionsKilled'] + match_data['info']['participants'][playerCounter]['neutralMinionsKilled']
                participantVisionScore = match_data['info']['participants'][playerCounter]['visionScore']


        # print(participantKills, participantAssists, participantDeaths, participantChamp, "vs", participantEnemyChamp, participantChampLevel, team)

                starting_items = []

                biggerNumber = playerCounter + 1

                for item in firstItems:
                    participantParticipantId = item.get('participantId')
                    if participantParticipantId is None:
                        continue
                    participantItemId = item.get('itemId')
            
                    isPurchased = item['type']

            # print("PARTID "+str(participantParticipantId))
            # print("BIGGER "+str(biggerNumber))
                    if participantParticipantId == biggerNumber and isPurchased == 'ITEM_PURCHASED':
                # print(item)
                        starting_items.append(participantItemId)

                    if isPurchased == 'ITEM_UNDO' and starting_items:
                        starting_items.pop()

        # print(starting_items)

                while len(starting_items) < 6:
                    starting_items.append(None) # 6 starting items columns in database so 6 variables so 6 values, so if only 2 starting items like dorans and potion then just none value
        # print(starting_items)

                startItem1, startItem2, startItem3, startItem4, startItem5, startItem6 = starting_items[:6] # single vlaues

        # print(startItem1, startItem2, startItem3, startItem4, startItem5, startItem6)

                final_items = [
                    match_data['info']['participants'][playerCounter].get(f'item{i}') for i in range(6)
                ]

                abilityOrder = []
                fullItems = []
                for frame in framesOverall:
                    events = frame['events']
                    for event in events:
                        if event.get('type') == 'SKILL_LEVEL_UP' and event.get('participantId') == biggerNumber:
                    # print(event)
                            abilityOrder.append(event.get('skillSlot'))
                        elif event.get('type') == 'ITEM_PURCHASED' and event.get('participantId') == biggerNumber:
                            item_id = event.get('itemId')
                            if item_id in fullItems:
                                continue # TUTAJ SKONCZYLES CHYBA NIE DODAJE SUPOPOT ITEMOW
                    
                            if item_id in boots_item_ids:
                                continue
                            if item_id not in final_items:
                                continue

                            if item_id in all_full_item_ids:
                        # print(event)
                                fullItems.append(item_id)
                        elif event.get('type') == 'ITEM_DESTROYED' and event.get('itemId') == 3867:

                            participantItemSupport = match_data['info']['participants'][playerCounter]
                            current_items = [
                            participantItemSupport.get(f'item{i}') for i in range(6)
                            ]

                # Check if any of the support_full_items replaced item 3867
                            replaced_by = next((item for item in current_items if item in support_full_items), None)
                            if replaced_by in fullItems:
                                continue
                            elif replaced_by:
                                fullItems.append(replaced_by)
                        # print(f"Relic Shield (3867) was replaced by support item {replaced_by}")

        # print(abilityOrder)
        # print("nastepny:")
        # print(fullItems)

                participant_items = {
                    participantItem1,
                    participantItem2,
                    participantItem3,
                    participantItem4,
                    participantItem5,
                    participantItem6,
                    participantItem7,
                }

                final_boots = next((item for item in participant_items if item in boots_item_ids), None)
        
                while len(abilityOrder) < 18:
                    abilityOrder.append(None) # 6 starting items columns in database so 6 variables so 6 values, so if only 2 starting items like dorans and potion then just none value
                # print(abilityOrder)

                trimmedAbilityOrder = abilityOrder[:18]
                abilityOrder1, abilityOrder2, abilityOrder3, abilityOrder4, abilityOrder5, abilityOrder6, abilityOrder7, abilityOrder8, abilityOrder9, abilityOrder10, abilityOrder11, abilityOrder12, abilityOrder13, abilityOrder14, abilityOrder15, abilityOrder16, abilityOrder17, abilityOrder18 = trimmedAbilityOrder
                padded_items = fullItems + [None] * (6 - len(fullItems))

                firstItem, secondItem, thirdItem, fourthItem, fifthItem, sixthItem = padded_items[:6]

                if biggerNumber == 1 or biggerNumber == 6:
                    participantRole = "1"
                elif biggerNumber == 2 or biggerNumber == 7:
                    participantRole = "2"
                elif biggerNumber == 3 or biggerNumber == 8:
                    participantRole = "3"
                elif biggerNumber == 4 or biggerNumber == 9:
                    participantRole = "4"
                elif biggerNumber == 5 or biggerNumber == 10:
                    participantRole = "5"

                print("---------------------------")
                print(participantTeam, participantKills, participantDeaths, participantAssists, participantChampLevel, participantChampKey)
                print(participantRune1, participantRune2, participantRune3, participantRune4, participantSideRune5, participantSideRune6, participantCircleRune7, participantCircleRune8, participantCircleRune9)
                print(participantSpell1, participantSpell2, participantItem1,participantItem2,participantItem3,participantItem4,participantItem5,participantItem6,participantItem7)
                print(participantRole,participantDamageDealt, participantEnemyChamp, participantLargestMultiKill, participantMinionsKilled, participantVisionScore)
                print(startItem1, startItem2, startItem3, startItem4, startItem5, startItem6)
                print(final_boots, firstItem, secondItem, thirdItem, fourthItem, fifthItem, sixthItem)
                print(abilityOrder)

                InsertIntoMatchInfoQuery = """
                INSERT INTO matchinfo (
                    matchId, userId, team, kills, deaths, assists, champLevel, champId,
                    rune1, rune2, rune3, rune4, sideRune5, sideRune6, circleRune7, circleRune8, circleRune9,
                    spell1, spell2,
                    item1, item2, item3, item4, item5, item6, item7,
                    role, damageDealt, enemyChampId, largestMultiKill, minionsKilled, visionScore,
                    startItem1, startItem2, startItem3, startItem4, startItem5, startItem6,
                    boots, firstItem, secondItem, thirdItem, fourthItem, fifthItem, sixthItem,
                    abilityOrder1, abilityOrder2, abilityOrder3, abilityOrder4, abilityOrder5, abilityOrder6, abilityOrder7, abilityOrder8, abilityOrder9,
                    abilityOrder10, abilityOrder11, abilityOrder12, abilityOrder13, abilityOrder14, abilityOrder15, abilityOrder16, abilityOrder17, abilityOrder18
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s,
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """

                InsertToMatchInfoValues = (
                match_id, user_id, participantTeam, participantKills, participantDeaths, participantAssists, participantChampLevel, participantChampKey,
                participantRune1, participantRune2, participantRune3, participantRune4, participantSideRune5, participantSideRune6,
                participantCircleRune7, participantCircleRune8, participantCircleRune9,
                participantSpell1, participantSpell2,
                participantItem1, participantItem2, participantItem3, participantItem4, participantItem5, participantItem6, participantItem7,
                participantRole, participantDamageDealt, participantEnemyChamp, participantLargestMultiKill, participantMinionsKilled, participantVisionScore,
                startItem1, startItem2, startItem3, startItem4, startItem5, startItem6,
                final_boots, firstItem, secondItem, thirdItem, fourthItem, fifthItem, sixthItem,
                *trimmedAbilityOrder  # make sure abilityOrder is a list of exactly 18 characters (fill with None if shorter)
                )

                cursor.execute(InsertIntoMatchInfoQuery, InsertToMatchInfoValues)
    

                playerCounter = playerCounter + 1
                enemyCounter = enemyCounter + 1
        
                if enemyCounter == 10:
                    enemyCounter = 0
                    team = 1

    else:
        print("Match already exists!")
    #print(all_full_items)

    db.commit()
    
cursor.close()
db.close()