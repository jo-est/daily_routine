
    def login(self):
        username = self.login_user.get().strip()
        password = self.login_pass.get()

        if not username or not password:
            messagebox.showwarning(
                "Missing Information",
                "Enter your username and password."
            )
            return

        with connect_db() as db:
            user = db.execute(
                "SELECT id, password FROM users WHERE username=?",
                (username,)
            ).fetchone()

        valid = False

        if user:
            stored = user[1]

            if stored.startswith("pbkdf2$"):
                parts = stored.split("$")
                if len(parts) == 3:
                    salt = parts[1]
                    saved_hash = parts[2]
                    entered_hash = hash_password(password, salt)
                    valid = hmac.compare_digest(
                        entered_hash, saved_hash
                    )
            else:
                # Support accounts from the earlier version.
                old_hash = hashlib.sha256(
                    password.encode("utf-8")
                ).hexdigest()

                valid = hmac.compare_digest(stored, old_hash)

                # Upgrade the old password hash after successful login.
                if valid:
                    salt = secrets.token_hex(16)
                    new_hash = (
                        "pbkdf2$" + salt + "$"
                        + hash_password(password, salt)
                    )
                    with connect_db() as db:
                        db.execute(
                            "UPDATE users SET password=? WHERE id=?",
                            (new_hash, user[0])
                        )

        if valid:
            self.user_id = user[0]
            self.username = username
            self.week_offset = 0
            self.show_tracker()
        else:
            messagebox.showerror(
                "Login Failed",
                "Incorrect username or password."
            )

