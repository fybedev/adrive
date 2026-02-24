from tools.db_auth import register_user
from lightdb import LightDB

db = LightDB()
db['users'] = []
db['files'] = {}

register_user('admin', 'admin', quota_gb=10, is_admin=True)
