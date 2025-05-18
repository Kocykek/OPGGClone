import mysql.connector
import requests
import re

# Database configuration
db_config = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'newpassword',
    'database': 'leaguestats'
}

# Connect to the MySQL database
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

# URL for the items data
url = "https://ddragon.leagueoflegends.com/cdn/15.9.1/data/en_US/item.json"

# Fetching the JSON data
response = requests.get(url)
data = response.json()

# Function to extract stats from description
def extract_stats_from_description(description):
    # Regular expression to extract stats inside <stats> tag and <attention> tags
    stats_pattern = re.compile(r'<stats>(.*?)</stats>', re.DOTALL)
    match = stats_pattern.search(description)
    
    stats = []
    if match:
        stats_str = match.group(1)  # Extracted string inside <stats>...</stats>
        # Split the stats by <br> and clean the tags
        stats = [re.sub(r'<attention>(.*?)</attention>', r'\1', stat).strip() for stat in stats_str.split('<br>')]
    return stats

# Function to clean up the description (remove all HTML tags and stats, replace <br> with spaces)
def clean_description(description):
    # Remove all stats part first
    description_no_stats = re.sub(r'<stats>.*?</stats>', '', description)
    
    # Replace <passive> tags with content followed by a colon
    description_no_stats = re.sub(r'<passive>(.*?)</passive>', r'\1:', description_no_stats)
    
    # Replace <active> tags with content followed by a colon
    description_no_stats = re.sub(r'<active>(.*?)</active>', r'\1:', description_no_stats)
    
    # Replace <br> with a space
    description_no_stats = description_no_stats.replace('<br>', ' ')
    
    # Then remove all other HTML tags
    clean_desc = re.sub(r'<.*?>', '', description_no_stats)
    return clean_desc.strip()

# Function to extract item details (including stats and cleaned description) from the fetched data
def extract_item_details(item_data):
    item_details = []
    isBoots = 0
    isFullItem = 0
    for item_id, item in item_data["data"].items():
        name = item.get("name", "N/A")
        description = item.get("description", "N/A")
        
        # Extracting stats from description
        stats = extract_stats_from_description(description)
        
        # Clean the description (remove HTML tags and stats, and format passives)
        cleaned_description = clean_description(description)
        
        # Extracting cost
        cost = item.get("gold", {}).get("total", "N/A")
        print(item.get('gold'))
        if item.get('into') is None and item.get('gold', {}).get('total', 0) > 899:
            isFullItem = 1
        elif item.get('into') is None and item.get('from') and item.get('from')[0] == "3867":
            isFullItem = 1
        else:
            isFullItem = 0

        tags = item.get('tags')
        for tag in tags:
            if tag == 'Boots':
                isBoots = 1
            else:
                isBoots = 0
        
        item_details.append({
            "name": name,
            "description": cleaned_description,
            "stats": ', '.join(stats) if stats else 'No stats available',
            "itemId": item_id,
            "cost": cost,
            "isBoots": isBoots,
            "isFullItem": isFullItem
        })

        print(isBoots)
    
    return item_details

# Get details for all items
item_details = extract_item_details(data)

# Insert the item details into the database
insert_query = """
    INSERT INTO items (name, description, stats, itemId, cost, isBoots, isFullItem)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
"""

for item in item_details:
    cursor.execute(insert_query, (item['name'], item['description'], item['stats'], item['itemId'], item['cost'], item['isBoots'], item['isFullItem']))

# Commit the changes and close the connection
conn.commit()
cursor.close()
conn.close()

print("Items successfully imported into the database.")
