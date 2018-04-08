import sqlite3


class DataBase:
    def __init__(self, id):
        self.conn = sqlite3.connect("users.db")
        self.cursor = self.conn.cursor()
        self.user_id = id

    def create_table(self):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS user_%s(word_id INT, english_word TEXT, translation TEXT, "
                            "completion INT)" % self.user_id)

    def insert_word(self, word_num, word, translation):
        self.cursor.execute("INSERT INTO user_%s (word_id, english_word, translation, completion) "
                            "VALUES(?, ?, ?, ?)" % self.user_id, (word_num, word, translation, 0))
        self.conn.commit()

    def read_dict(self):
        self.cursor.execute("SELECT * FROM user_%s" % self.user_id)
        return self.cursor.fetchall()

    def delete_dict(self):
        self.cursor.execute("DELETE FROM user_%s" % self.user_id)
        self.conn.commit()

    def close(self):
        self.cursor.close()
        self.conn.close()
