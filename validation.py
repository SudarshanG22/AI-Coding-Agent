def validate_username(username):
    if not username:
        return False, "Username must be provided"

    if not username.isalnum():
        return False, "Username must contain only alphanumeric characters"

    return True, ""