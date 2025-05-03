import mysql.connector
import glob

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="newpassword",
    database="leaguestats"
)
cursor = conn.cursor()

for filename in sorted(glob.glob("insert_commands_*.sql") + glob.glob("update_commands_*.sql")):
    print(f"Executing {filename}...")
    with open(filename, "r", encoding="utf-8") as file:
        statements = file.read().split(";") # splitting by semicolon so every insert/update is single
        for stmt in statements:
            stmt = stmt.strip()
            if stmt:
                cursor.execute(stmt)

conn.commit()
cursor.close()
conn.close()
