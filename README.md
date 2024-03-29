
# Telegram Jira Bot 

This project contains a Telegram bot that creates tasks in Jira based on messages from allowed users. The bot is designed to run in a Docker container, making it easy to deploy and run.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- Docker
- Docker Compose

You also need a Telegram bot token and Jira API token.

## Setup

1. **Clone the repository:**

```bash
git clone <repository-url>
cd <repository-name>
```

2. **Configure environment variables:**
Copy the .env.example file to a new file named .env:
```bash
cp .env.example .env
```
Edit the .env file with your actual values:
```env
TG_BOT_TOKEN=your_telegram_bot_token
JIRA_TOKEN=your_jira_api_token_encoded_in_base64
JIRA_URL=https://your-jira-instance.atlassian.net/rest/api/3/issue
JIRA_PROJECT_KEY=your_project_key
JIRA_ISSUE_TYPE=Task
ASSIGNEE_ACCOUNT_ID=your_jira_account_id
ALLOWED_USER_ID=telegram_user_id_allowed_to_create_tasks
```
Instructions for creating a Telegram bot can be found at [Telegram Bot Tutorial](https://core.telegram.org/bots/tutorial#getting-ready).    
How to obtain your Jira token: [Manage API tokens for your Atlassian account](https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/).   
To find out your Telegram user ID, you can use [My Telegram ID Bot](https://t.me/myidbot).   

3. **Build and start the bot:**
Run the following command to build the Docker image and start the bot:
```bash
docker compose up --build
```
The bot will start and run in the background.

## Usage
Once the bot is running, the allowed user can send messages to the bot on Telegram. Each message will create a new task in Jira with the message text as the task summary.

## Development
To make changes to the bot, edit the `bot.py` file. After making changes, rebuild the Docker image and restart the container:
```bash
docker compose up --build --force-recreate
```
## License
This project is open-source and available under the MIT License.
