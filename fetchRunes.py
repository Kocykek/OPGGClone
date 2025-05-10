import json
import re
import mysql.connector

# Load rune JSON data
with open("runesReforged.json", "r", encoding="utf-8") as file:
    runes_data = json.load(file)

# MySQL DB config
db_config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'newpassword',
    'database': 'leaguestats'
}

conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# Function to clean HTML tags and format text
def clean_description(text):
    # Replace known HTML tags and keywords
    text = re.sub(r"<br\s*/?>", " ", text)
    text = re.sub(r"</?b>", "", text)
    text = re.sub(r"<i>(.*?)</i>", r"'\1'", text)
    text = re.sub(r"<.*?>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# Prepare SQL insert
insert_query = """
    INSERT INTO runes (runeKeyId, name, description, originalGameID)
    VALUES (%s, %s, %s, %s)
"""

# Mapping of rune tree names to runeKeyId from runesKey table
rune_key_map = {
    "Domination": 1,
    "Inspiration": 2,
    "Precision": 3,
    "Resolve": 4,
    "Sorcery": 5
}

# Loop through each rune tree
for tree in runes_data:
    runeKeyId = rune_key_map.get(tree["name"], None)
    if runeKeyId is None:
        continue

    for slot in tree["slots"]:
        for rune in slot["runes"]:
            name = rune["name"]
            originalId = rune['id']
            description = clean_description(rune.get("longDesc", ""))
            cursor.execute(insert_query, (runeKeyId, name, description, originalId))

# Commit and close
conn.commit()
cursor.close()
conn.close()
print("Runes imported successfully.")
