import telebot
import os
import requests
import json
import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

# Logging configuration
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# Load environment variables from .env file
load_dotenv()

# Environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
JIRA_TOKEN = os.getenv('JIRA_TOKEN')
JIRA_API_URL = os.getenv('JIRA_API_URL')
JIRA_WEB_URL = os.getenv('JIRA_WEB_URL')
JIRA_PROJECT_KEY = os.getenv('JIRA_PROJECT_KEY')
JIRA_ISSUE_TYPE = os.getenv('JIRA_ISSUE_TYPE')
ASSIGNEE_ACCOUNT_ID = os.getenv('ASSIGNEE_ACCOUNT_ID')
PAVEL_ACCOUNT_ID = os.getenv('PAVEL_ACCOUNT_ID')
# List of allowed user IDs
ALLOWED_USER_IDS_STR = os.getenv('ALLOWED_USER_IDS', '')
ALLOWED_USER_IDS = [int(uid.strip()) for uid in ALLOWED_USER_IDS_STR.split(',') if uid.strip()]

# Check critical environment variables
if not TELEGRAM_BOT_TOKEN:
    logging.error("TG_BOT_TOKEN is not set. Check your .env file.")
    exit(1)

if not JIRA_TOKEN:
    logging.error("JIRA_TOKEN is not set. Check your .env file.")
    exit(1)

if not JIRA_API_URL:
    logging.error("JIRA_API_URL is not set. Check your .env file.")
    exit(1)

if not JIRA_PROJECT_KEY:
    logging.error("JIRA_PROJECT_KEY is not set. Check your .env file.")
    exit(1)

if not ASSIGNEE_ACCOUNT_ID:
    logging.error("ASSIGNEE_ACCOUNT_ID is not set. Check your .env file.")
    exit(1)

if not PAVEL_ACCOUNT_ID:
    logging.error("PAVEL_ACCOUNT_ID is not set. Check your .env file.")
    exit(1)

if not ALLOWED_USER_IDS:
    logging.error("ALLOWED_USER_IDS is not set. Check your .env file.")
    exit(1)

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# Temporary storage for user data
user_data = {}

def get_epics():
    headers = {
        "Accept": "application/json",
        "Authorization": f"Basic {JIRA_TOKEN}"
    }
    query = {
        "jql": f"project = {JIRA_PROJECT_KEY} AND issuetype = Epic",
        "fields": "summary"
    }
    response = requests.get(f"{JIRA_API_URL}/search", headers=headers, params=query)
    logging.debug(f"Jira API Response: {response.status_code}, {response.text}")
    if response.status_code == 200:
        issues = response.json().get('issues', [])
        return {issue['id']: issue['fields']['summary'] for issue in issues}
    else:
        logging.error(f"Failed to fetch epics: {response.text}")
        return {}

def create_jira_issue(summary, description, epic_id, assignee_id):
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Basic {JIRA_TOKEN}"
    }
    payload = json.dumps({
        "fields": {
            "project": {
                "key": JIRA_PROJECT_KEY
            },
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "text": description,
                                "type": "text"
                            }
                        ]
                    }
                ]
            },
            "issuetype": {
                "name": JIRA_ISSUE_TYPE
            },
            "assignee": {
                "id": assignee_id
            },
            "parent": {
                "id": epic_id
            }
        }
    })
    api_url = f"{JIRA_API_URL}/issue"
    logging.debug(f"Creating Jira Issue with payload: {payload}")
    response = requests.post(api_url, headers=headers, data=payload)
    logging.debug(f"Jira API Response: {response.status_code}, {response.text}")
    if response.status_code == 201:
        issue_key = response.json().get('key')
        return f"Task successfully created: {JIRA_WEB_URL}/browse/{issue_key}"
    else:
        logging.error(f"Failed to create task in Jira. Status Code: {response.status_code}")
        return "Failed to create task in Jira."

def get_epics_markup(epics):
    markup = InlineKeyboardMarkup()
    for epic_id, epic_name in epics.items():
        markup.add(InlineKeyboardButton(epic_name, callback_data=f"epic_{epic_id}"))
    markup.add(InlineKeyboardButton("❌ Cancel", callback_data="cancel"))
    return markup

def get_cancel_markup():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("❌ Cancel", callback_data="cancel"))
    return markup

def get_assignee_markup():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Me", callback_data="assignee_me"),
        InlineKeyboardButton("👤 Pavel", callback_data="assignee_pavel")
    )
    markup.add(InlineKeyboardButton("❌ Cancel", callback_data="cancel"))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id in ALLOWED_USER_IDS:
        user_data[message.from_user.id] = {}
        bot.reply_to(message, "Please enter the task summary:")
    else:
        bot.reply_to(message, "You are not authorized to use this bot.")
        logging.warning(f"Unauthorized access attempt by user {message.from_user.id}.")

@bot.message_handler(func=lambda message: message.from_user.id in ALLOWED_USER_IDS)
def handle_message(message):
    user_id = message.from_user.id

    if user_id not in user_data or 'summary' not in user_data[user_id]:
        user_data[user_id] = {'summary': message.text}
        bot.reply_to(message, "Please enter the task description:", reply_markup=get_cancel_markup())
    elif 'description' not in user_data[user_id]:
        user_data[user_id]['description'] = message.text
        bot.send_message(message.chat.id, "Please choose an assignee:", reply_markup=get_assignee_markup())
    else:
        bot.reply_to(message, "Unexpected error. Please start again with /start.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("assignee_"))
def select_assignee(call):
    user_id = call.from_user.id

    if call.data == "assignee_me":
        assignee_id = ASSIGNEE_ACCOUNT_ID
    elif call.data == "assignee_pavel":
        assignee_id = PAVEL_ACCOUNT_ID
    else:
        bot.send_message(call.message.chat.id, "Invalid selection.")
        return

    user_data[user_id]['assignee_id'] = assignee_id

    epics = get_epics()
    if not epics:
        bot.send_message(call.message.chat.id, "Failed to fetch epics. Please try again later.")
        del user_data[user_id]
        return

    user_data[user_id]['epics'] = epics
    bot.send_message(call.message.chat.id, "Please choose an epic:", reply_markup=get_epics_markup(epics))
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("epic_"))
def select_epic(call):
    user_id = call.from_user.id
    epic_id = call.data.split("_")[1]

    if user_id in user_data and epic_id in user_data[user_id].get('epics', {}):
        summary = user_data[user_id]['summary']
        description = user_data[user_id]['description']
        assignee_id = user_data[user_id]['assignee_id']

        response_message = create_jira_issue(summary, description, epic_id, assignee_id)
        bot.send_message(call.message.chat.id, response_message)
        del user_data[user_id]
    else:
        bot.send_message(call.message.chat.id, "Invalid epic selected. Please start again with /start.")

    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def cancel_creation(call):
    user_id = call.from_user.id
    if user_id in user_data:
        del user_data[user_id]
        bot.send_message(call.message.chat.id, "Task creation has been canceled.")
        logging.info(f"Task creation canceled by user {user_id}")
    else:
        bot.send_message(call.message.chat.id, "No task creation process to cancel.")
    bot.answer_callback_query(call.id)

if __name__ == "__main__":
    logging.info("Bot is running...")
    bot.polling()