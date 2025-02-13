import sqlite3


class DatabaseManager:
    @staticmethod
    def get_contacts():
        """Register a new user."""
        print("IN GET CONTACTS")
        try:
            with sqlite3.connect('users.db') as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT username FROM users')
                results = cursor.fetchall()
                usernames = []
                for row in results:
                    usernames.append(row[0])
                print("found these users:",usernames)
                return usernames
        # except sqlite3.IntegrityError:
        #     return "ERROR§Username already exists"
        except Exception as e:
            print(f"ERROR§Fetching contacts failed: {str(e)}")
            return f"ERROR§Fetching contacts failed: {str(e)}"

    # @staticmethod
    def get_limits(username):
        print("IN GET CONTACTS")
        try:
            with sqlite3.connect('users.db') as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT username FROM users')
                results = cursor.fetchall()
                usernames = []
                for row in results:
                    usernames.append(row[0])
                print(usernames)
                return usernames
        # except sqlite3.IntegrityError:
        #     return "ERROR§Username already exists"
        except Exception as e:
            print(f"ERROR§Fetching contacts failed: {str(e)}")
            return f"ERROR§Fetching contacts failed: {str(e)}"


    def delete_account(username):
        try:
            with sqlite3.connect('users.db') as conn:
                cursor = conn.cursor()
                
                # Start a transaction
                cursor.execute('BEGIN TRANSACTION')
                try:
                    # todo: Delete user's messages (both sent and received)
                    
                    # Delete user from users table
                    cursor.execute('''
                        DELETE FROM users 
                        WHERE username = ?
                    ''', (username,))
                    
                    # Delete from any other related tables (e.g., settings, inbox)
                    # cursor.execute('''
                    #     DELETE FROM user_settings 
                    #     WHERE username = ?
                    # ''', (username,))
                    
                    # Commit the transaction
                    conn.commit()
                    print(f"Successfully deleted account for user: {username}")
                    return True
                    
                except Exception as e:
                    # If any error occurs, rollback the transaction
                    cursor.execute('ROLLBACK')
                    print(f"Error deleting account: {str(e)}")
                    return False
        except sqlite3.Error as e:
            print(f"Database error: {str(e)}")
            return False
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return False