import bcrypt
from lightdb import LightDB

l_db = LightDB()


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def _is_bcrypt_hash(value: str) -> bool:
    return isinstance(value, str) and value.startswith(('$2a$', '$2b$', '$2y$')) and len(value) >= 60


def _check_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


def register_user(username: str, password: str, quota_gb: int = 5, is_admin: bool = False) -> None:
    global l_db

    if 'users' not in l_db:
        l_db['users'] = []
    if 'files' not in l_db:
        l_db['files'] = {}

    users = l_db['users']
    for i, user in enumerate(users):
        if user.get('username') == username:
            updated = dict(user)
            updated['password'] = _hash_password(password)
            updated['quota_gb'] = quota_gb
            updated['is_admin'] = is_admin
            users[i] = updated
            return

    user = {
        'username': username,
        'password': _hash_password(password),
        'quota_gb': quota_gb,
        'is_admin': is_admin
    }
    l_db['users'].append(user)

def check_if_user_exists(username: str) -> bool:
    global l_db
    if 'users' not in l_db:
        return False
    for user in l_db['users']:
        if user.get('username') == username:
            return True
    return False

def list_users() -> list:
    global l_db
    return l_db['users']

def is_admin_user(username: str) -> bool:
    global l_db
    if 'users' not in l_db:
        return False
    for user in l_db['users']:
        if user.get('username') == username:
            return bool(user.get('is_admin', False))
    return False

def check_if_auth(username: str, password: str) -> bool:
    global l_db
    if 'users' not in l_db:
        return False
    for user in l_db['users']:
        if user.get('username') != username:
            continue

        stored_password = user.get('password')
        if not stored_password:
            return False

        if _is_bcrypt_hash(stored_password):
            return _check_password(password, stored_password)

        if stored_password == password:
            user['password'] = _hash_password(password)
            return True

        return False
    return False
