import os
import time
import json
import random
from datetime import datetime
from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired,
    ChallengeRequired,
    BadPassword,
    TwoFactorRequired,
    MediaNotFound,
    UserNotFound,
    PrivateAccount,
    ClientThrottledError
)
import logger

# ------------------- Configuration -------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config_rules.json")
PROCESSED_COMMENTS_FILE = os.path.join(SCRIPT_DIR, "processed_comments.json")
SESSION_FILE = os.path.join(SCRIPT_DIR, "session.json")

# Credentials (use environment variables or fallback)
IG_USERNAME = os.getenv("IG_USERNAME", "Amilliondollarscene")
IG_PASSWORD = os.getenv("IG_PASSWORD", "moujmaker5717572")

# Load proxy list from config
PROXIES = []
try:
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
        PROXIES = cfg.get('proxies', [])
except Exception:
    PROXIES = []

# Initialize client
cl = Client()

# ------------------- Helper Functions -------------------

def pick_proxy():
    """Randomly choose a proxy from the list."""
    return random.choice(PROXIES) if PROXIES else None


def safe_fetch_comments(post_id, amount=20, max_backoff=300):
    """Fetch comments with exponential backoff on throttle."""
    backoff = 1
    while True:
        try:
            return cl.media_comments(post_id, amount=amount)
        except ClientThrottledError as e:
            wait = getattr(e, 'retry_after', backoff * 2)
            logger.log_warning(f"Throttled fetching comments. Sleeping {wait}s", "RateLimit")
            time.sleep(wait)
            backoff = min(backoff * 2, max_backoff)
        except Exception as e:
            logger.log_error(f"Error fetching comments: {e}", "Fetch Error")
            return []


def safe_send_dm(user_id, username, text, max_backoff=300):
    """Send DM with exponential backoff on throttle."""
    backoff = 1
    while True:
        try:
            cl.direct_send(text, user_ids=[user_id])
            logger.log_success(f"DM sent to @{username}", "Message Sent")
            return True
        except ClientThrottledError as e:
            wait = getattr(e, 'retry_after', backoff * 2)
            logger.log_warning(f"Throttled sending DM. Sleeping {wait}s", "RateLimit")
            time.sleep(wait)
            backoff = min(backoff * 2, max_backoff)
        except (UserNotFound, PrivateAccount) as e:
            logger.log_error(f"DM failed to @{username}: {e}", "DM Error")
            return False
        except Exception as e:
            logger.log_error(f"Unexpected DM error @{username}: {e}", "DM Error")
            return False


def load_rules(filename=CONFIG_FILE):
    """Loads rules (and proxies) from a JSON file."""
    logger.log_process(f"Loading rules from {filename}...", "Config")
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            rules = data.get('rules') if isinstance(data, dict) else data
            if not isinstance(rules, list):
                logger.log_warning("Rules format invalid, expecting a list", "Config Error")
                return []
            logger.log_success(f"Loaded {len(rules)} rules", "Config")
            return rules
    except Exception as e:
        logger.log_error(f"Error loading rules: {e}", "Config Error")
        return []


def load_processed_comments():
    """Loads processed comment IDs to avoid duplicate DM."""
    if not os.path.exists(PROCESSED_COMMENTS_FILE):
        return {}
    try:
        with open(PROCESSED_COMMENTS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {k: set(v) for k, v in data.items() if isinstance(v, list)}
    except Exception as e:
        logger.log_error(f"Error loading processed comments: {e}", "Data Error")
        return {}


def save_processed_comments(data):
    """Saves processed comment IDs."""
    try:
        serializable = {k: list(v) for k, v in data.items()}
        with open(PROCESSED_COMMENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(serializable, f, indent=2)
        logger.log_success("Processed comments saved", "Data")
    except Exception as e:
        logger.log_error(f"Error saving processed comments: {e}", "Data Error")


def login_user():
    """Authenticate with session persistence and 2FA support."""
    logger.log_process("Starting login...", "Auth")
    if os.path.exists(SESSION_FILE):
        try:
            cl.load_settings(SESSION_FILE)
            cl.login(IG_USERNAME, IG_PASSWORD)
            logger.log_success("Logged in via session file", "Auth")
            return True
        except Exception:
            logger.log_warning("Session expired, performing fresh login", "Auth")
    try:
        cl.login(IG_USERNAME, IG_PASSWORD)
        cl.dump_settings(SESSION_FILE)
        logger.log_success("Fresh login successful", "Auth")
        return True
    except TwoFactorRequired:
        code = logger.console.input("Enter 2FA code: ").strip()
        cl.login(IG_USERNAME, IG_PASSWORD, verification_code=code)
        cl.dump_settings(SESSION_FILE)
        logger.log_success("Logged in with 2FA", "Auth")
        return True
    except Exception as e:
        logger.log_error(f"Login failed: {e}", "Auth Error")
        return False


def get_post_id_from_link(post_link):
    """Convert Instagram post link to post ID using instagrapi."""
    try:
        return cl.media_pk_from_url(post_link)
    except Exception as e:
        logger.log_error(f"Failed to convert post link to ID: {post_link} ({e})", "Config Error")
        return None

# ------------------- Main Bot Loop -------------------
if __name__ == "__main__":
    logger.show_startup_banner()
    if not login_user():
        logger.log_error("Authentication failed, exiting...", "Fatal")
        exit(1)

    rules = load_rules()
    if not rules:
        logger.log_error("No rules loaded, check config_rules.json", "Fatal")
        exit(1)

    # Convert post_link to post_id for each rule at startup
    for rule in rules:
        post_link = rule.get('post_link')
        if post_link:
            post_id = get_post_id_from_link(post_link)
            if post_id:
                rule['post_id'] = post_id
            else:
                logger.log_error(f"Could not resolve post_id for rule: {rule.get('rule_id')}", "Config Error")
        else:
            logger.log_error(f"No post_link found for rule: {rule.get('rule_id')}", "Config Error")

    processed = load_processed_comments()
    cycle = 0
    try:
        while True:
            cycle += 1
            logger.show_cycle_header(cycle)

            # Optional proxy rotation per cycle
            proxy = pick_proxy()
            if proxy:
                cl.set_proxy(proxy)
                logger.log_info(f"Using proxy {proxy}", "Proxy")

            for rule in rules:
                rule_id = rule.get('rule_id')
                post_id = rule.get('post_id')  # Now always numeric ID, resolved from post_link
                keyword = str(rule.get('special_number', '')).lower()
                reply_msg = rule.get('message_to_send')

                if not post_id:
                    logger.log_warning(f"Skipping rule {rule_id}: post_id not resolved", "Config Error")
                    continue

                comments = safe_fetch_comments(post_id)
                for c in comments:
                    cid = str(c.pk)
                    if cid in processed.get(rule_id, set()):
                        continue
                    if c.text and c.text.strip().lower() == keyword:
                        logger.show_match_found(cid, c.user.username, keyword, rule_id)
                        if safe_send_dm(c.user.pk, c.user.username, reply_msg):
                            processed.setdefault(rule_id, set()).add(cid)
                    time.sleep(random.uniform(0.3, 1.0))  # human-like pause

            save_processed_comments(processed)

            # Randomized cycle delay
            wait = random.uniform(25, 40)
            logger.log_info(f"Sleeping {wait:.1f}s before next cycle", "Scheduler")
            time.sleep(wait)

    except KeyboardInterrupt:
        logger.log_warning("Interrupted by user, saving state...", "Shutdown")
        save_processed_comments(processed)
        logger.log_info("Bot stopped.", "Shutdown")
    except Exception as e:
        logger.log_error(f"Unexpected error: {e}", "Critical")
        save_processed_comments(processed)
