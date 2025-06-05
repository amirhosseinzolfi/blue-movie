import os
import time
import json
from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired,
    ChallengeRequired,
    BadPassword,
    TwoFactorRequired,
    MediaNotFound,
    UserNotFound,
    PrivateAccount
)
from datetime import datetime
import logger

# Constants
IG_USERNAME = "Amilliondollarscene"
IG_PASSWORD = "moujmaker5717572"
PROCESSED_COMMENTS_FILE = "processed_comments.json"
SESSION_FILE = "session.json"
CONFIG_RULES_FILE = "config_rules.json"

# Initialize Client
cl = Client()

def load_rules(filename=CONFIG_RULES_FILE):
    """Loads rules from a JSON file."""
    logger.log_process(f"Loading rules from {filename}...")
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            rules = json.load(f)
            if not isinstance(rules, list):
                logger.log_warning(f"Content of {filename} is not a list", "Invalid Format")
                return []
            logger.log_success(f"Successfully loaded {len(rules)} rules", "Rules Loaded")
            return rules
    except FileNotFoundError:
        logger.log_error(f"Rules file {filename} not found", "File Not Found")
        return []
    except json.JSONDecodeError:
        logger.log_error(f"Error decoding JSON from {filename}", "JSON Error")
        return []
    except Exception as e:
        logger.log_error(f"Unexpected error loading rules: {e}", "Load Error")
        return []

def login_user():
    """Logs in the user, handling session persistence, interactive 2FA, and common exceptions."""
    logger.log_process("Initializing login process...", "Authentication")
    
    session_loaded_successfully = False
    if os.path.exists(SESSION_FILE):
        logger.log_info(f"Found existing session file: {SESSION_FILE}")
        try:
            with logger.status_context("[cyan]Loading session data...", spinner="dots"):
                cl.load_settings(SESSION_FILE)
            logger.log_success("Session data loaded successfully")
            
            with logger.status_context("[cyan]Authenticating with session...", spinner="dots"):
                cl.login(IG_USERNAME, IG_PASSWORD)
            logger.log_success("Login successful using saved session", "Session Login")
            return True
        except LoginRequired:
            logger.log_warning("Session expired or invalid, proceeding to fresh login")
        except BadPassword:
            logger.log_warning("Password may have changed, proceeding to fresh login")
        except Exception as e:
            logger.log_error(f"Session login failed: {e}")
    
    logger.log_process("Attempting fresh login...", "Fresh Authentication")
    try:
        with logger.status_context("[cyan]Logging in...", spinner="dots"):
            cl.login(IG_USERNAME, IG_PASSWORD)
        logger.log_success("Login successful without 2FA", "Fresh Login")
        
        with logger.status_context("[cyan]Saving session...", spinner="dots"):
            cl.dump_settings(SESSION_FILE)
        logger.log_success(f"Session saved to {SESSION_FILE}")
        return True
    except TwoFactorRequired:
        logger.log_warning("2FA code required", "Two-Factor Authentication")
        try:
            user_2fa_code = logger.console.input("[cyan]Enter your 2FA code: [/cyan]").strip()
            if not user_2fa_code:
                logger.log_error("No 2FA code entered", "Authentication Failed")
                return False
            
            with logger.status_context("[cyan]Verifying 2FA code...", spinner="dots"):
                cl.login(IG_USERNAME, IG_PASSWORD, verification_code=user_2fa_code)
            logger.log_success("Login successful with 2FA", "2FA Authentication")
            
            with logger.status_context("[cyan]Saving session...", spinner="dots"):
                cl.dump_settings(SESSION_FILE)
            logger.log_success("Session saved successfully")
            return True
        except BadPassword:
            logger.log_error("Invalid credentials during 2FA", "Authentication Error")
            return False
        except Exception as e:
            logger.log_error(f"2FA login failed: {e}", "2FA Error")
            return False
    except ChallengeRequired:
        logger.log_error("Challenge required - please login manually first", "Challenge Required")
        return False
    except BadPassword:
        logger.log_error("Invalid password provided", "Authentication Error")
        return False
    except Exception as e:
        logger.log_error(f"Unexpected login error: {e}", "Login Error")
        return False

def load_processed_comments():
    """Loads processed comment data (dict) from a JSON file with error handling."""
    logger.log_process(f"Loading processed comments from {PROCESSED_COMMENTS_FILE}...")
    
    if not os.path.exists(PROCESSED_COMMENTS_FILE):
        logger.log_info(f"No existing processed comments file found")
        return {}
    try:
        with open(PROCESSED_COMMENTS_FILE, 'r') as f:
            content = f.read()
            if not content:
                logger.log_info("Processed comments file is empty")
                return {}
            data = json.loads(content)
            if not isinstance(data, dict):
                logger.log_error("Invalid format in processed comments file", "Format Error")
                return {}
            
            migrated_data = {}
            for key, value in data.items():
                if isinstance(value, set):
                    migrated_data[key] = list(value)
                elif isinstance(value, list):
                    migrated_data[key] = value
                else:
                    logger.log_warning(f"Invalid value type for rule '{key}', initializing as empty list")
                    migrated_data[key] = []
            
            total_comments = sum(len(ids) for ids in migrated_data.values())
            logger.log_success(f"Loaded {total_comments} processed comments across {len(migrated_data)} rules", "Comments Loaded")
            return migrated_data
    except json.JSONDecodeError:
        logger.log_error("JSON decode error in processed comments file", "Decode Error")
        return {}
    except IOError as e:
        logger.log_error(f"IO error reading processed comments: {e}", "IO Error")
        return {}
    except Exception as e:
        logger.log_error(f"Unexpected error loading processed comments: {e}", "Load Error")
        return {}

def save_processed_comments(processed_data):
    """Saves processed comment data (dict) to a JSON file with error handling."""
    try:
        with open(PROCESSED_COMMENTS_FILE, 'w') as f:
            json.dump(processed_data, f, indent=2)
        count = sum(len(ids) for ids in processed_data.values())
        logger.log_success(f"Saved {count} processed comments across {len(processed_data)} rules", "Data Saved")
    except IOError as e:
        logger.log_error(f"IO error saving processed comments: {e}", "Save Error")
    except Exception as e:
        logger.log_error(f"Unexpected error saving processed comments: {e}", "Save Error")

def fetch_comments(post_id):
    """Fetches recent comments for a given post_id with error handling."""
    try:
        comments = cl.media_comments(post_id, amount=20)
        return comments
    except MediaNotFound:
        logger.log_error(f"Post not found: {post_id}", "Media Error")
        return []
    except Exception as e:
        logger.log_error(f"Error fetching comments for post {post_id}: {e}", "Fetch Error")
        return []

def send_direct_message(user_id, username, text):
    """Sends a direct message to a user with error handling."""
    try:
        cl.direct_send(text, user_ids=[user_id])
        logger.log_success(f"DM sent to @{username}", "Message Sent")
        return True
    except UserNotFound:
        logger.log_error(f"User not found: @{username}", "User Error")
        return False
    except PrivateAccount:
        logger.log_error(f"Cannot DM private account: @{username}", "Private Account")
        return False
    except Exception as e:
        logger.log_error(f"DM failed to @{username}: {e}", "DM Error")
        return False

if __name__ == "__main__":
    logger.show_startup_banner()
    
    if login_user():
        logger.console.print()
        logger.log_info("Authentication successful, initializing bot...", "Ready")
        
        rules = load_rules()
        if not rules:
            logger.log_error("No rules loaded. Check config_rules.json", "Configuration Error")
            exit()
        
        logger.console.print()
        logger.show_rules_table(rules)
        logger.console.print()
        
        processed_data = load_processed_comments()
        initial_total_processed = sum(len(v) for v in processed_data.values())
        
        cycle_count = 0
        try:
            while True: 
                cycle_count += 1
                logger.show_cycle_header(cycle_count)
                
                any_new_comment_processed_this_cycle = False
                total_comments_checked = 0
                total_matches_found = 0

                for rule in rules:
                    rule_id = rule.get('rule_id')
                    post_id = rule.get('post_id')
                    special_number = rule.get('special_number')
                    message_to_send = rule.get('message_to_send')

                    if not all([rule_id, post_id, special_number, message_to_send]):
                        logger.log_warning(f"Incomplete rule configuration: {rule_id}", "Rule Skipped")
                        continue
                    
                    comments = fetch_comments(post_id)
                    total_comments_checked += len(comments)
                    
                    logger.show_rule_processing(rule_id, post_id, special_number, len(comments))
                    
                    if not comments:
                        continue

                    processed_comments_list_for_rule = processed_data.get(rule_id, [])
                    processed_comments_set_for_rule = set(processed_comments_list_for_rule)
                    
                    new_comments_processed_for_this_rule = False

                    for comment in comments:
                        comment_pk_str = str(comment.pk)
                        
                        if comment_pk_str in processed_comments_set_for_rule:
                            continue

                        if comment.text == special_number:
                            total_matches_found += 1
                            logger.show_match_found(comment_pk_str, comment.user.username, special_number, rule_id)
                            
                            dm_sent = send_direct_message(comment.user.pk, comment.user.username, message_to_send)
                            if dm_sent:
                                if rule_id not in processed_data:
                                    processed_data[rule_id] = []
                                processed_data[rule_id].append(comment_pk_str)
                                new_comments_processed_for_this_rule = True
                                any_new_comment_processed_this_cycle = True

                # Show cycle summary
                logger.show_cycle_summary(
                    total_comments_checked,
                    total_matches_found,
                    sum(len(ids) for ids in processed_data.values())
                )

                if any_new_comment_processed_this_cycle:
                    save_processed_comments(processed_data)
                else:
                    logger.log_info("No new matches found this cycle")
                
                sleep_duration = 30
                logger.console.print()
                with logger.status_context(f"[cyan]Waiting {sleep_duration} seconds for next cycle...", spinner="dots"):
                    time.sleep(sleep_duration)
                logger.console.print()
        
        except KeyboardInterrupt:
            logger.console.print()
            logger.log_warning("Bot interrupted by user", "Shutdown")
            save_processed_comments(processed_data)
            logger.log_info("Final state saved. Goodbye! 👋")
        except Exception as e:
            logger.console.print()
            logger.log_error(f"Unexpected error in main loop: {e}", "Critical Error")
            save_processed_comments(processed_data)

    else:
        logger.log_error("Authentication failed. Cannot start bot", "Startup Failed")
