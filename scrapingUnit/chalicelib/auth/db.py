# Database Connector (SQlite3)
# Store & Fetch data from sqlite
import sqlite3


def create_connection():
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    db_file = "chalicelib/auth/db.sqlite3"
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Exception as e:
        print(e)

    return conn


def run_query(conn, query):
    try:
        c = conn.cursor()
        c.execute(query)
        conn.commit()
        return c
    except Exception as e:
        print(e)


def create_tables():
    """
        Create tables with database connection
        Table names: users
        """
    conn = create_connection()
    query = """
        CREATE TABLE IF NOT EXISTS users (
            id integer PRIMARY KEY,
            username text NOT NULL,
            password text NOT NULL
        );
    """
    run_query(conn=conn, query=query)
    conn.close()


def create_user(username, password):
    """
        Create new user with name and password
        """
    conn = create_connection()
    query = f"INSERT INTO users(username, password) VALUES ('{username}', '{password}')"
    run_query(conn=conn, query=query)
    conn.close()


def get_user(user_name, password):
    """
        Fetch User's data by username
    """
    # conn = create_connection()
    # query = f"SELECT * from users where username='{user_name}' and password='{password}'"
    # cursor = run_query(conn, query)
    # result = cursor.fetchone()
    # conn.close()
    # print(result)
    users = [
        {
            "username": "vishal",
            "password": "75VW7bdCpG",
        },
        {
            "username": "johannes",
            "password": "password",
        },
    ]

    for user in users:
        if user['username'] == user_name and user['password'] == password:
            return True
    return False
