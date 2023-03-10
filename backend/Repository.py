from models.File import Status
from shared.Singleton import Singleton
from Database import Database
from models.User import User

print(b"hello")
INSERT_USER = (
    "INSERT INTO users (user_name, password, public_key) VALUES (%s, %s, %s) RETURNING user_id;"
)

INSERT_FILE = (
    "INSERT INTO files (user_id, file_name, upload_time) VALUES (%s, %s, %s) RETURNING file_id;"
)

INSERT_REQUEST = (
    "INSERT INTO requests (file_id, sender_id, status, sent_at) VALUES (%s, %s, %s, %s);"
)

UPDATE_USER_SID = (
    "UPDATE users SET sid = %s WHERE user_id = %s;"
)

UPDATE_USER_PUBLIC_KEY = (
    "UPDATE users SET public_key = %s WHERE user_id = %s;"
)

UPDATE_REQUEST = (
    "UPDATE requests SET status = %s, enc_master_key = %s WHERE (file_id, sender_id) = (%s, %s);"
)

GET_USER_BY_ID = (
    "SELECT * FROM users WHERE user_id = %s;"
)

GET_USER_BY_NAME = (
    "SELECT * FROM users WHERE user_name = %s;"
)

GET_FILE_BY_ID = (
    "SELECT * FROM users LEFT JOIN files ON users.user_id = files.user_id WHERE users.user_id = files.user_id AND files.file_id = %s;"
)

GET_ALL_FILES = (
    """SELECT f.file_id, f.file_name, f.user_id, u.user_name, f.upload_time
    FROM files f 
    INNER JOIN users u ON f.user_id = u.user_id;"""
)

GET_USER_REQUESTS = (
    """ SELECT files.file_id, files.file_name, requests.sender_id, u1.user_name AS sender_name, files.user_id AS receiver_id, 
                u2.user_name AS receiver_name, requests.status, requests.sent_at, requests.enc_master_key, u1.public_key
        FROM files INNER JOIN requests ON files.file_id = requests.file_id
        INNER JOIN users u1 ON requests.sender_id = u1.user_id
        INNER JOIN users u2 ON files.user_id = u2.user_id 
        WHERE (requests.sender_id = %s OR files.user_id = %s) ; """
)

GET_REQUEST = (
    """ SELECT files.file_id, files.file_name, requests.sender_id, u1.user_name AS sender_name, files.user_id AS receiver_id, 
                u2.user_name AS receiver_name, requests.status, requests.sent_at, requests.enc_master_key, u1.public_key
        FROM files INNER JOIN requests ON files.file_id = requests.file_id
        INNER JOIN users u1 ON requests.sender_id = u1.user_id
        INNER JOIN users u2 ON files.user_id = u2.user_id 
        WHERE (files.file_id = %s AND requests.sender_id = %s) ; """
)

DELETE_REQUEST = (
    "DELETE FROM requests WHERE (file_id, sender_id) = (%s, %s);"
)


class Repository(metaclass=Singleton):

    def __init__(self, database: Database) -> None:
        self.database = Database()

    def insert_user(self, user_name: str, password: str, public_key: bytes):
        c = self.database.connection.cursor()
        c.execute(INSERT_USER, (user_name, password, public_key))
        user_id = c.fetchone()
        self.database.connection.commit()
        return user_id[0]

    def insert_file(self, user_id: int, file_name: str, upload_time: str) -> int:
        c = self.database.connection.cursor()
        c.execute(INSERT_FILE, (user_id, file_name, upload_time))
        file_id = c.fetchone()
        self.database.connection.commit()
        return file_id[0]

    def insert_request(self, file_id: int, sender_id: int, status: int, sent_at: str):
        c = self.database.connection.cursor()
        c.execute(INSERT_REQUEST, (file_id, sender_id, status, sent_at))
        self.database.connection.commit()

    def get_request(self, file_id: int, sender_id: int):
        c = self.database.connection.cursor()
        c.execute(GET_REQUEST, (file_id, sender_id))
        res = c.fetchone()
        self.database.connection.commit()
        keys = ("file_id", "file_name", "sender_id", "sender_name", "receiver_id",
                "receiver_name", "status", "sent_at", "enc_master_key", "public_key")
        r = {keys[i]: v for i, v in enumerate(res)}
        if r["enc_master_key"] is not None:
            r["enc_master_key"] = r["enc_master_key"].tobytes()
        if r["public_key"] is not None:
            r["public_key"] = r["public_key"].tobytes()
        r["status"] = Status(r["status"]).name
        return r

    def update_user_sid(self, sid, user_id):
        c = self.database.connection.cursor()
        c.execute(UPDATE_USER_SID, (sid, user_id))
        self.database.connection.commit()

    def update_user_pkey(self, public_key, user_id):
        c = self.database.connection.cursor()
        c.execute(UPDATE_USER_SID, (public_key, user_id))
        self.database.connection.commit()

    def update_request(self, status, enc_master_key, file_id, sender_id):
        c = self.database.connection.cursor()
        c.execute(UPDATE_REQUEST, (status, enc_master_key, file_id, sender_id))
        self.database.connection.commit()

    def get_file_with_user(self, file_id):
        c = self.database.connection.cursor()
        c.execute(GET_FILE_BY_ID, (file_id,))
        res = c.fetchone()
        self.database.connection.commit()
        return res

    def get_user(self, user_id) -> User:
        c = self.database.connection.cursor()
        c.execute(GET_USER_BY_ID, (user_id,))
        res = c.fetchone()
        self.database.connection.commit()
        return User(res[0], res[1], res[2], res[3], res[4])

    def get_user_by_name(self, user_name) -> User:
        c = self.database.connection.cursor()
        c.execute(GET_USER_BY_NAME, (user_name,))
        res = c.fetchone()
        self.database.connection.commit()
        if res != None:
            return User(res[0], res[1], res[2], res[3], res[4])
        return None

    def get_all_files(self):
        c = self.database.connection.cursor()
        c.execute(GET_ALL_FILES)
        res = c.fetchall()
        self.database.connection.commit()
        keys = ("id", "name", "owner_id", "owner_name", "uploaded_at")
        allFiles = []
        for r in res:
            r = {keys[i]: v for i, v in enumerate(r)}
            allFiles.append(r)
        return allFiles

    def get_user_requests(self, user_id: int):
        c = self.database.connection.cursor()
        c.execute(GET_USER_REQUESTS, (user_id, user_id))
        res = c.fetchall()
        self.database.connection.commit()
        keys = ("file_id", "file_name", "sender_id", "sender_name", "receiver_id",
                "receiver_name", "status", "sent_at", "enc_master_key", "public_key")
        allRequests = []
        for r in res:
            r = {keys[i]: v for i, v in enumerate(r)}
            if r["enc_master_key"] is not None:
                r["enc_master_key"] = r["enc_master_key"].tobytes()
            if r["public_key"] is not None:
                r["public_key"] = r["public_key"].tobytes()
            r["status"] = Status(r["status"]).name
            allRequests.append(r)
        return allRequests

    def delete_request(self, file_id, sender_id):
        c = self.database.connection.cursor()
        c.execute(DELETE_REQUEST, (file_id, sender_id))
        self.database.connection.commit()
