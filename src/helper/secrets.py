from src.helper.obfuscation_loader import retrieve_obfuscated_key

def load_secret_key(key_name):
    try:
        return retrieve_obfuscated_key(key_name)
    except Exception as e:
        raise RuntimeError(f"An error occurred while reading the secret key: {e}")
