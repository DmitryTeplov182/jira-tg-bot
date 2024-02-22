import telebot
import os
import requests
import json

# Load environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TG_BOT_TOKEN')
JIRA_TOKEN = os.getenv('JIRA_TOKEN')
JIRA_URL = os.getenv('JIRA_URL')
JIRA_PROJECT_KEY = os.getenv('JIRA_PROJECT_KEY')
JIRA_ISSUE_TYPE = os.getenv('JIRA_ISSUE_TYPE')
ASSIGNEE_ACCOUNT_ID = os.getenv('ASSIGNEE_ACCOUNT_ID')
ALLOWED_USER_ID = int(os.getenv('ALLOWED_USER_ID'))

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

def create_jira_issue(summary):
    # Set the request headers
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Basic {JIRA_TOKEN}"
    }
    # Define the payload for the POST request
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
                                "text": "Task created via Telegram Bot",
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
                "id": ASSIGNEE_ACCOUNT_ID
            }
        }
    })
    # Send the request to JIRA
    response = requests.post(JIRA_URL, headers=headers, data=payload)
    # Handle the response
    if response.status_code == 201:
        issue_key = response.json().get('key')
        issue_url = f"https://pushflow.atlassian.net/browse/{issue_key}"
        return f"Task successfully created and assigned: {issue_url}"
    else:
        return "Failed to create task in Jira."

@bot.message_handler(func=lambda message: message.from_user.id == ALLOWED_USER_ID)
def handle_message(message):
    summary = message.text
    response_message = create_jira_issue(summary)
    bot.reply_to(message, response_message)

if __name__ == "__main__":
    bot.polling()
