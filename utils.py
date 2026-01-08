from flask import redirect as fredirect
import json

def redirect(url):
    return fredirect(url)

def dbload():
    with open('db.json', 'r') as f:
        return json.load(f)

def dbsave(obj):
    with open('db.json', 'w') as f:
        json.dump(obj, f)
        
def udbload():
    with open('users.json', 'r') as f:
        return json.load(f)
    
def udbsave(obj):
    with open('users.json', 'w') as f:
        json.dump(obj, f)