import sqlite3


class DataBase:
    def __init__(self):
        self.conn = sqlite3.connect("users.db")
        self.cursor = self.conn.cursor()
        self.user_first_name = None
        self.user_last_name = None

    def create_table(self, user_first_name, user_last_name):
        self.user_first_name = user_first_name
        self.user_last_name = user_last_name
        self.cursor.execute("CREATE TABLE IF NOT EXISTS %s_%s(word_id INT, english_word TEXT, translation TEXT)"
                            % (user_first_name, user_last_name))

    def inserting(self, word_num, word, translation):
        try:
            self.cursor.execute("INSERT INTO %s_%s (word_id, english_word, translation) VALUES(?, ?, ?)"
                                % (self.user_first_name, self.user_last_name), (word_num, word, translation))
            self.conn.commit()
        except Exception as e:
            print(e)

    def close(self):
        self.cursor.close()
        self.conn.close()
