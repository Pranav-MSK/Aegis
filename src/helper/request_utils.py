# cython: language_level=3
from flask import request

def get_form_value(key, default):
    value = str(request.form.get(key, default))
    return value.strip() if value.strip() else default
