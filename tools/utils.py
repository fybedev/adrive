from flask import redirect as fredirect
import json

def redirect(url):
    return fredirect(url)