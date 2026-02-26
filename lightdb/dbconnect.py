import sqlite3
import os
import yaml

def get_connection():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'db.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    db_path = os.path.join(os.path.dirname(__file__), '..', config['DATABASE_LOCATION'])
    conn = sqlite3.connect(db_path, check_same_thread=False)
    return conn
