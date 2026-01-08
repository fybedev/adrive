from utils import *

db = dbload()
db['files'].pop("I_Love_You_-_Boy_Next_Door_1.mp3_45475777")
dbsave(db)