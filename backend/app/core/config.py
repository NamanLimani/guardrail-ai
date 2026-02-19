# This key is used to digitally sign the tokens.
# In production, this would come from an Environment Variable (.env).
# For now, we will hardcode a random string.
SECRET_KEY = "guardrail_super_secret_key_change_this_in_prod"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30