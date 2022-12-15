import sqlite3


class BotDB:

    def __init__(self, db_file):
        self.db = sqlite3.connect(db_file)
        self.cursor = self.db.cursor()

    def user_exists(self, user_id):
        result = self.cursor.execute("SELECT `id` FROM `users` WHERE `user_id` = ?", (user_id,))
        return bool(len(result.fetchall()))

    def user_exists_bylogin(self, login):
        result = self.cursor.execute("SELECT `login` FROM `users` WHERE `login` = ?", (login,))
        return bool(len(result.fetchall()))

    def user_exists_byusername(self, username):
        result = self.cursor.execute("SELECT `username` FROM `users` WHERE `username` = ?", (username,))
        return bool(len(result.fetchall()))

    def get_password(self, login):
        result = self.cursor.execute("SELECT `password` FROM `users` WHERE `login` = ?", (login,))
        return result.fetchone()[0]

    def update_last_login(self, user_id):
        result = self.cursor.execute("UPDATE `users` SET 'last_login' = datetime('now', 'localtime') WHERE `user_id` = ?", (
            user_id,))
        return self.db.commit()

    def update_user_id(self, user_id, login):
        result = self.cursor.execute("UPDATE `users` SET `user_id` = ? WHERE `login` = ?", (
            user_id,
            login,))
        return self.db.commit()

    def update_user_id_byuserid(self, user_id, user_id1):
        result = self.cursor.execute("UPDATE `users` SET `user_id` = ? WHERE `user_id` = ?", (
            user_id,
            user_id1,))
        return self.db.commit()

    def get_user_id(self, login):
        result = self.cursor.execute("SELECT `user_id` FROM `users` WHERE `login` = ?", (login,))
        return result.fetchone()[0]

    def get_userdata(self, user_id):
        result = self.cursor.execute("SELECT * FROM `users` WHERE `user_id` = ?", (user_id,))
        return result.fetchall()[0]

    def get_userdata_bylogin(self, login):
        result = self.cursor.execute("SELECT * FROM `users` WHERE `login` = ?", (login,))
        return result.fetchall()[0]

    def get_all_userdata(self):
        result = self.cursor.execute("SELECT * FROM `users`")
        return result.fetchall()

    def remove_bonuse(self, name):
        result = self.cursor.execute("DELETE FROM `bonuses` WHERE `name` = ?", (name,))
        return self.db.commit()

    def rename_bonuse(self, name, new_name):
        result = self.cursor.execute("UPDATE 'bonuses' SET `name` = ? WHERE `name` = ?", (new_name, name,))
        return self.db.commit()

    def add_bonuse(self, data, name, desc):
        result = self.cursor.execute("INSERT INTO `bonuses` (`data`, 'name', 'description') VALUES (?, ?, ?)", (
                             data,
                             name,
                             desc))
        return self.db.commit()

    def set_wishlist(self, user_id, wishlist):
        result = self.cursor.execute("UPDATE 'users' SET `wishlist` = ? WHERE `user_id` = ?", (wishlist, user_id,))
        return self.db.commit()

    def rename_user(self, login, name):
        result = self.cursor.execute("UPDATE 'users' SET `username` = ? WHERE `login` = ?", (name, login,))
        return self.db.commit()

    def set_login(self, login, new_login):
        result = self.cursor.execute("UPDATE 'users' SET `login` = ? WHERE `login` = ?", (new_login, login,))
        return self.db.commit()

    def set_password(self, password, login):
        result = self.cursor.execute("UPDATE 'users' SET `password` = ? WHERE `login` = ?", (password, login,))
        return self.db.commit()

    def user_set_points(self, login, points):
        result = self.cursor.execute("UPDATE 'users' SET `points` = ? WHERE `login` = ?", (points, login,))
        return self.db.commit()

    def add_user(self, user_id, username, login, password, depart):
        result = self.cursor.execute("INSERT INTO `users` (`user_id`, 'username', 'login', 'password', 'depart') VALUES (?, ?, ?, ?, ?)", (
                             user_id,
                             username,
                             login,
                             password,
                             depart))
        return self.db.commit()

    def remove_user(self, login):
        result = self.cursor.execute("DELETE FROM `users` WHERE `login` = ?", (login,))
        return self.db.commit()

    def get_bonuses_names(self):
        result = self.cursor.execute("SELECT * FROM `bonuses`")
        return result.fetchall()

    def get_bonuse_bydata(self, data):
        result = self.cursor.execute("SELECT * FROM `bonuses` WHERE 'data' = ?", (data,))
        return result.fetchall()

    def get_bonuse_byname(self, name):
        result = self.cursor.execute("SELECT * FROM `bonuses` WHERE 'name' = ?", (name,))
        return result.fetchall()

    def get_allusernames(self):
        result = self.cursor.execute("SELECT username, login, points FROM `users`")
        return result.fetchall()

    def get_usernames_bydep(self, depart):
        result = self.cursor.execute("SELECT username, login, points FROM `users` WHERE `depart` = ?", (depart,))
        return result.fetchall()

    def get_all_bonuses_log(self):
        result = self.cursor.execute("SELECT * FROM `logs` WHERE `type` = ?", ('bonuses_use',))
        return result.fetchall()

    def write_log(self, type, user_id, login, action):
        result = self.cursor.execute("INSERT INTO `logs` (`type`, 'user_id', 'login', 'action') VALUES (?, ?, ?, ?)", (
                             type,
                             user_id,
                             login,
                             action))
        return self.db.commit()

    def write_bonuse_log(self, type, user_id, login, action, bonuse, file_id):
        result = self.cursor.execute("INSERT INTO `logs` (`type`, 'user_id', 'login', 'action', 'bonuse', 'file_id') VALUES (?, ?, ?, ?, ?, ?)", (
                             type,
                             user_id,
                             login,
                             action,
                             bonuse,
                             file_id))
        return self.db.commit()

    """def get_username(self, user_id):
        result = self.cursor.execute("SELECT `username` FROM `users` WHERE `user_id` = ?", (user_id,))
        return result.fetchone()[0]

    def add_record(self, user_id, operation, value):
        self.cursor.execute("INSERT INTO `records` (`users_id`, `operation`, `value`) VALUES (?, ?, ?)",
                            (self.get_user_id(user_id),
                             operation == "+",
                             value))
        return self.db.commit()

    def get_records(self, user_id, within="all"):

        if (within == "day"):
            result = self.cursor.execute(
                "SELECT * FROM `records` WHERE `users_id` = ? AND `date` BETWEEN datetime('now', 'start of day') AND datetime('now', 'localtime') ORDER BY `date`",
                (self.get_user_id(user_id),))
        elif (within == "week"):
            result = self.cursor.execute(
                "SELECT * FROM `records` WHERE `users_id` = ? AND `date` BETWEEN datetime('now', '-6 days') AND datetime('now', 'localtime') ORDER BY `date`",
                (self.get_user_id(user_id),))
        elif (within == "month"):
            result = self.cursor.execute(
                "SELECT * FROM `records` WHERE `users_id` = ? AND `date` BETWEEN datetime('now', 'start of month') AND datetime('now', 'localtime') ORDER BY `date`",
                (self.get_user_id(user_id),))
        else:
            result = self.cursor.execute("SELECT * FROM `records` WHERE `users_id` = ? ORDER BY `date`",
                                         (self.get_user_id(user_id),))

        return result.fetchall()"""

    def close(self):
        """Закрываем соединение с БД"""
        self.db.close()
