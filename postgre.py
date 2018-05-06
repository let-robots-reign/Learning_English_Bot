import psycopg2


class DataBase:
    def __init__(self, id):
        self.conn = psycopg2.connect("")
        self.cursor = self.conn.cursor()
        self.user_id = id

    def create_table(self):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS user_{} "
                            "(english_word varchar, translation varchar, completion integer);".format(self.user_id))

    def insert_word(self, word, translation):
        self.cursor.execute("INSERT INTO user_{} (english_word, translation, completion) "
                            "VALUES (%s, %s, %d);".format(self.user_id), (word, translation, 0))
        self.conn.commit()

    def select_uncompleted_words(self):
        self.cursor.execute("SELECT english_word, translation FROM user_{} WHERE completion < 100;".format(self.user_id))
        return self.cursor.fetchall()

    def increment_completion(self, word):
        current_completion = self.cursor.execute("SELECT completion FROM user_{} "
                                                 "WHERE english_word = %s;".format(self.user_id), (word,)).fetchall()
        self.cursor.execute("UPDATE user_{} SET completion = %d WHERE english_word = %s;".format(self.user_id),
                            (current_completion[0][0] + 20, word))
        self.conn.commit()

    def read_dict(self):
        self.cursor.execute("SELECT * FROM user_{};".format(self.user_id))
        return self.cursor.fetchall()

    def delete_word(self, word):
        self.cursor.execute("DELETE FROM user_{} WHERE english_word = %s;".format(self.user_id), (word,))
        self.conn.commit()

    def delete_dict(self):
        self.cursor.execute("DELETE FROM user_{};".format(self.user_id))
        self.conn.commit()

    def close(self):
        self.cursor.close()
        self.conn.close()
