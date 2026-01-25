from lightdb import LightDB

l_db = LightDB()


def register_user(username: str, password: str, quota_gb: int = 5) -> None:
    global l_db
    
    user = {
        'username': username,
        'password': password,
        'quota_gb': quota_gb
    }
    l_db['users'].append(user)

def check_if_user_exists(username: str) -> bool:
    global l_db
    for user in l_db['users']:
        if user.get('username') == username:
            return True
    return False

def list_users() -> list:
    global l_db
    return l_db['users']

def check_if_auth(username: str, password: str) -> bool:
    global l_db
    for user in l_db['users']:
        if user.get('username') == username and user.get('password') == password:
            return True
    return False
