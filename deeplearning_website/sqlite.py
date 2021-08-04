import sqlite3
# Creating the DB and what not
conn = sqlite3.connect('socialMedia.db')
c = conn.cursor()


c.execute("""CREATE TABLE dogpics(
    username text,
    dogimage text,
    caption text
)
""")
conn.commit()

c.execute("""CREATE TABLE catpics(
    username text,
    catimage text,
    caption text
)
""")

conn.commit()

#c.execute("INSERT INTO media VALUES (?,?)",('jflo','Text describing the picture'))
