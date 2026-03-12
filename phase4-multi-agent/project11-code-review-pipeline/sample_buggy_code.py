# sample_buggy_code.py
# User Management Module — AcmeCorp Internal Tools v2.1
# Author: dev-team
# Last modified: 2024-03-15
#
# NOTE: This file contains intentional bugs for the code review exercise.
# In a real project, these would be serious security and reliability issues.

# Import sqlite3 for database operations
import sqlite3

# Import os for environment variable access
import os

# Import hashlib for password hashing
import hashlib

# Import json — imported but never used in this file (unused import bug)
import json

# Import re — imported but never used in this file (unused import bug)
import re

# The database file path — hardcoded (should be in config or env variable)
DATABASE_PATH = "users.db"


def get_user_by_username(username):
    """
    Retrieve a user record from the database by username.

    BUG 1 (CRITICAL - SQL INJECTION): The username is directly concatenated
    into the SQL query string. An attacker could pass:
    username = "admin' OR '1'='1"
    and the query becomes: SELECT * FROM users WHERE username = 'admin' OR '1'='1'
    This returns ALL users. The fix is to use parameterized queries.
    """
    # Open a connection to the database
    conn = sqlite3.connect(DATABASE_PATH)

    # Create a cursor to execute SQL
    cursor = conn.cursor()

    # CRITICAL BUG: String concatenation in SQL query = SQL injection vulnerability
    # An attacker can manipulate this query to access unauthorized data
    query = "SELECT * FROM users WHERE username = '" + username + "'"

    # Execute the vulnerable query
    cursor.execute(query)

    # Fetch the matching user record
    result = cursor.fetchone()

    # Close the connection (at least this is done)
    conn.close()

    # Return the result
    return result


def calculate_average_score(scores):
    """
    Calculate the average score from a list of numeric values.

    BUG 2 (CRITICAL - DIVISION BY ZERO): If an empty list is passed,
    len(scores) is 0 and dividing by 0 causes a ZeroDivisionError crash.
    The fix is to check if the list is empty before dividing.
    """
    # Sum all the scores in the list
    total = sum(scores)

    # CRITICAL BUG: No check for empty list — will crash with ZeroDivisionError
    # If scores = [], then len(scores) = 0 and total / 0 raises an exception
    average = total / len(scores)

    # Return the calculated average
    return average


def find_duplicate_users(user_list):
    """
    Find users that appear more than once in a list.

    BUG 3 (WARNING - O(n²) PERFORMANCE): The nested loop checks every pair
    of users. For 1,000 users, this does 1,000,000 comparisons.
    The fix is to use a set or dictionary for O(n) performance.
    """
    # List to store users that appear more than once
    duplicates = []

    # WARNING BUG: O(n²) nested loop — extremely slow for large user lists
    # Outer loop: go through each user
    for i in range(len(user_list)):
        # Inner loop: compare with every other user
        for j in range(len(user_list)):
            # Skip comparing a user with itself
            if i != j:
                # Check if these two positions have the same username
                if user_list[i] == user_list[j]:
                    # Check if we already added this duplicate
                    if user_list[i] not in duplicates:
                        # Add to duplicates list
                        duplicates.append(user_list[i])

    # Return the list of duplicate usernames
    return duplicates


def create_new_user(username, password, email):
    """
    Create a new user in the database.

    BUG 4 (CRITICAL - SQL INJECTION): Same SQL injection issue as get_user.
    BUG 5 (WARNING - MISSING INPUT VALIDATION): No validation that username,
    password, or email are valid before inserting into the database.
    Empty strings, None values, or malformed emails will be stored.
    BUG 6 (WARNING - PLAIN TEXT PASSWORD): The password is stored without
    proper hashing. Even with hashlib imported, it is not being used here.
    """
    # Open a database connection
    conn = sqlite3.connect(DATABASE_PATH)

    # Create a cursor
    cursor = conn.cursor()

    # WARNING BUG: No validation — username could be empty string or None
    # WARNING BUG: No email format validation
    # WARNING BUG: Password stored in plain text (hashlib is imported but not used!)
    # CRITICAL BUG: SQL injection via string formatting
    query = "INSERT INTO users (username, password, email) VALUES ('" + username + "', '" + password + "', '" + email + "')"

    # Execute the vulnerable insert query
    cursor.execute(query)

    # Commit the transaction
    conn.commit()

    # Close the connection
    conn.close()

    # Return success message
    return f"User {username} created successfully"


def get_all_users_with_role(role):
    """
    Retrieve all users who have a specific role.

    BUG 7 (CRITICAL - SQL INJECTION): Again using string concatenation.
    An attacker could pass role = "admin' UNION SELECT username, password FROM users--"
    to dump the entire password database.
    """
    # Open database connection
    conn = sqlite3.connect(DATABASE_PATH)

    # Create cursor
    cursor = conn.cursor()

    # CRITICAL BUG: SQL injection vulnerability in role parameter
    query = "SELECT username, email FROM users WHERE role = '" + role + "'"

    # Execute the query
    cursor.execute(query)

    # Fetch all matching records
    results = cursor.fetchall()

    # Close the connection
    conn.close()

    # Return the results
    return results


def update_user_email(user_id, new_email):
    """
    Update the email address for a user identified by their ID.

    BUG 8 (WARNING - MISSING VALIDATION): No check that user_id is a positive
    integer or that new_email is a valid email format.
    BUG 9 (CRITICAL - SQL INJECTION): Same pattern as other functions.
    """
    # Open database connection
    conn = sqlite3.connect(DATABASE_PATH)

    # Create cursor
    cursor = conn.cursor()

    # WARNING BUG: user_id could be negative, zero, or a string
    # WARNING BUG: new_email could be anything — no format validation
    # CRITICAL BUG: SQL injection via string formatting
    query = "UPDATE users SET email = '" + new_email + "' WHERE id = " + str(user_id)

    # Execute the update
    cursor.execute(query)

    # Commit changes
    conn.commit()

    # Close connection
    conn.close()

    # Return confirmation
    return "Email updated"


def search_users_by_name(search_term):
    """
    Search for users whose name contains the search term.
    Returns a list of matching users.

    BUG 10 (CRITICAL - SQL INJECTION): String formatting used in LIKE query.
    BUG 11 (WARNING - NO RESULT LIMIT): Could return thousands of rows with
    no pagination, potentially causing memory issues on large databases.
    """
    # Open database connection
    conn = sqlite3.connect(DATABASE_PATH)

    # Create cursor
    cursor = conn.cursor()

    # CRITICAL BUG: SQL injection via format string in LIKE clause
    # WARNING BUG: No LIMIT clause — could return unlimited results
    query = "SELECT * FROM users WHERE name LIKE '%" + search_term + "%'"

    # Execute the search
    cursor.execute(query)

    # Fetch ALL results — no pagination!
    all_results = cursor.fetchall()

    # Close connection
    conn.close()

    # Return all results
    return all_results
