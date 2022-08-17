from http.cookies import SimpleCookie
from ast import literal_eval
from datetime import datetime


def get_cookie_data(app):
    """
        Retrieve google credentials and user information stored in cookie
        :param app: application object
        :return: mixed, mixed
    """
    req = app.current_request
    cookieData = req.headers.get('Cookie', '')
    cookie = SimpleCookie()
    cookie.load(cookieData)

    logged_user = None
    try:
        if cookie.get('credentials'):
            logged_user = literal_eval(cookie.get('credentials').value)
    except Exception as e:
        print(e)
    return logged_user


def is_authorized(app):
    """
        Check if the authorization was expired or not , and check credentials is not None

        :param  {} credentials
        :return boolean
    """
    logged_user = get_cookie_data(app)
    return logged_user and datetime.fromtimestamp(logged_user.get('expires_at', 0)) > datetime.now()
