import requests
from datetime import datetime
import mysql.connector
# Riot API key
API_KEY = "api here"

headers = {
    "X-Riot-Token": API_KEY
}

db_config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'newpassword',
    'database': 'leaguestats'
}

db = mysql.connector.connect(**db_config)

cursor = db.cursor(dictionary=True)
cursor.execute("SELECT puuid, whatdivisiontierId FROM summoners ORDER BY RAND() LIMIT 1")
user_data = cursor.fetchone()
print(user_data)
puuid = user_data['puuid']
whatDivision = user_data['whatdivisiontierId']
# Match ID and endpoint
match_id = "EUW1_7395354073"
region = "europe"


matchesUrl = f"https://{region}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=100" 
responseMatches = requests.get(matchesUrl, headers=headers)
listOfMatches = responseMatches.json()

onlyOneMatchID = listOfMatches[0]
print(onlyOneMatchID)
print(listOfMatches)

match_id = onlyOneMatchID
url = f"https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}"

# Make the API request
response = requests.get(url, headers=headers)
match_data = response.json()

# Extract and process relevant match info
match_name = match_id

select_query = "SELECT 1 FROM matches WHERE matchName = %s LIMIT 1"
cursor.execute(select_query, (match_name,))
match_exists = cursor.fetchone()
print(match_exists)

select_query = "SELECT * FROM items WHERE isBoots = 1"
cursor.execute(select_query)
boots_items = cursor.fetchall()

select_query = "SELECT itemId FROM items WHERE isFullItem = 1"
cursor.execute(select_query)
all_full_items = cursor.fetchall()
all_full_item_ids = {item['itemId'] for item in all_full_items}



if match_exists == None:
    timelineUrl = f"https://{region}.api.riotgames.com/lol/match/v5/matches/{match_id}/timeline"
    responseTimeline = requests.get(timelineUrl, headers=headers)
    timeline_data = responseTimeline.json()


    match_type = match_data["info"]["queueId"]
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
    print("Match Info:")
    print(f"Match Name   : {match_name}")
    print(f"Match Type   : {match_type}")
    print(f"Match Start  : {match_start}")
    print(f"Duration     : {match_duration} seconds")
    print(bans)
    print(game_ended_early)
    print("Did team 1 win?", match_win)

    insert_query = """
        INSERT INTO matches (matchName, matchType, matchStart, matchDuration, isRemake, ban1, ban2, ban3, ban4, ban5, ban6, ban7, ban8, ban9, ban10, win, whatDivisionTier )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query,(match_name, match_type, match_start, match_duration,game_ended_early, ban1, ban2, ban3, ban4, ban5, ban6, ban7, ban8, ban9, ban10, match_win, whatDivision))
    db.commit()




selectId_query = "SELECT matchId from matches WHERE matchName = %s LIMIT 1"
cursor.execute(selectId_query, (match_name,))
match_identificator = cursor.fetchone()
print("test")
print(match_identificator['matchId'])

# FETCHING PARTICIPANTS INFO NOW! [matchInfo] table

playerCounter = 0
enemyCounter = 5
team = 0


firstItems =  timeline_data['info']['frames'][1]['events']
framesOverall = timeline_data['info']['frames']

for participant in match_data['metadata']['participants']:
    participantPuuid = participant

    participantTeam = team
    
    participantKills = match_data['info']['participants'][playerCounter]['kills']
    participantDeaths = match_data['info']['participants'][playerCounter]['deaths']
    participantAssists = match_data['info']['participants'][playerCounter]['assists']
    participantChampLevel = match_data['info']['participants'][playerCounter]['champLevel']
    participantChamp = match_data['info']['participants'][playerCounter]['championName']

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
    participantEnemyChamp = match_data['info']['participants'][enemyCounter]['championName']
    participantLargestMultiKill = match_data['info']['participants'][playerCounter]['largestMultiKill']
    participantMinionsKilled = match_data['info']['participants'][playerCounter]['totalMinionsKilled'] + match_data['info']['participants'][playerCounter]['neutralMinionsKilled']
    participantVisionScore = match_data['info']['participants'][playerCounter]['visionScore']


    print(participantKills, participantAssists, participantDeaths, participantChamp, "vs", participantEnemyChamp, participantChampLevel, team)

    starting_items = []

    biggerNumber = playerCounter + 1

    for item in firstItems:
        participantParticipantId = item.get('participantId')
        if participantParticipantId is None:
            continue
        participantItemId = item.get('itemId')
        
        isPurchased = item['type']

        print("PARTID "+str(participantParticipantId))
        print("BIGGER "+str(biggerNumber))
        if participantParticipantId == biggerNumber and isPurchased == 'ITEM_PURCHASED':
            print(item)
            starting_items.append(participantItemId)

        if isPurchased == 'ITEM_UNDO' and starting_items:
            starting_items.pop()

    print(starting_items)

    while len(starting_items) < 6:
        starting_items.append(None) # 6 starting items columns in database so 6 variables so 6 values, so if only 2 starting items like dorans and potion then just none value
    print(starting_items)

    startItem1, startItem2, startItem3, startItem4, startItem5, startItem6 = starting_items # single vlaues

    print(startItem1, startItem2, startItem3, startItem4, startItem5, startItem6)

    abilityOrder = []
    fullItems = []
    for frame in framesOverall:
        events = frame['events']
        for event in events:
            if event.get('type') == 'SKILL_LEVEL_UP' and event.get('participantId') == biggerNumber:
                print(event)
                abilityOrder.append(event.get('skillSlot'))
            elif event.get('type') == 'ITEM_PURCHASED' and event.get('participantId') == biggerNumber:
                item_id = event.get('itemId')
                if item_id in all_full_item_ids:
                    print(event)
                    fullItems.append(item_id)
    print(abilityOrder)
    print(fullItems)
    while len(abilityOrder) < 18:
        abilityOrder.append(None) # 6 starting items columns in database so 6 variables so 6 values, so if only 2 starting items like dorans and potion then just none value
    print(abilityOrder)

    abilityOrder1, abilityOrder2, abilityOrder3, abilityOrder4, abilityOrder5, abilityOrder6, abilityOrder7, abilityOrder8, abilityOrder9, abilityOrder10, abilityOrder11, abilityOrder12, abilityOrder13, abilityOrder14, abilityOrder15, abilityOrder16, abilityOrder17, abilityOrder18 = abilityOrder


    playerCounter = playerCounter + 1
    enemyCounter = enemyCounter + 1
    
    if enemyCounter == 10:
        enemyCounter = 0
        team = 1


#print(all_full_items)


cursor.close()
db.close()