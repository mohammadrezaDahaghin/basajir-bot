import requests
from requests.auth import HTTPBasicAuth
from telebot import apihelper
import json
import telebot
from telebot.async_telebot import AsyncTeleBot
import asyncio
import hashlib
from telebot import types
import os
import schedule
import time
import getpass


#telebot Token
TOKEN ="6463346745:AAGtSlb2baBQSWF7dwT-xnj4sksE9ApOwxc"
bot = telebot.TeleBot(TOKEN)

# Jira base URL
base_url = 'https://jira.basa.ir'

# Authentication endpoint
auth_url = f'{base_url}/jira/rest/auth/1/session'
# searchIsue endpoint
getissue_url = f'{base_url}/jira/rest/api/2/search'

os.environ['SESSION_VALUE'] = ''     # Jira session token
os.environ['JIRA_USERNAME'] = ''     # Jira username
os.environ['JIRA_PASSWORD'] = ''     # Jira password
os.environ['CHAT_ID'] = ''           # Telegram chat ID

# Initialize variables for tracking issues and user actions
previous_issue_count = 0             # Count of previous issues
previous_issues = {}                 # Dictionary to store previous issues
last_start_command_time = {}          # Dictionary to track the time of last /start command
user_logged_in = {}                  # Dictionary to track user login status


headers = {
  "Accept": "application/json",
  "Content-Type": "application/json"
}

    #handle Request auth
def authenticate_and_get_session(username, password):

    data = {"username": username, "password": password}
    response = requests.post(auth_url, json=data, headers=headers)
    if response.status_code == 200:
        session_value = response.json()['session']['value']
        os.environ['SESSION_VALUE'] = session_value
        os.environ['JIRA_USERNAME'] = username
        os.environ['JIRA_PASSWORD'] = password
        return session_value
    else:
        return None

def get_issues(session_value):
    IssueLoad = json.dumps({
        "jql": f"assignee = {username} AND statusCategory = 2",
        "maxResults": None
    })

    headers_iss = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {session_value}"
    }

    auth = HTTPBasicAuth(os.getenv('JIRA_USERNAME'), os.getenv('JIRA_PASSWORD'))

    response = requests.post(getissue_url, data=IssueLoad, headers=headers_iss, auth=auth)

    if response.status_code == 200:
        return response.json().get('issues', [])
    else:
        return None


    #handle start comment
@bot.message_handler(commands=['start'])
def start_message(message):

    global last_start_command_time

    user_id = message.chat.id
    current_time = time.time()
    time_limit = 15  # Time limit in seconds

    if os.getenv('SESSION_VALUE') in last_start_command_time:
        last_time = last_start_command_time[os.getenv('SESSION_VALUE')]
        if current_time - last_time < time_limit:
            bot.send_message(message.chat.id, "شما نمی‌توانید `/start` را بیش از یک بار در {} ثانیه ارسال کنید.".format(time_limit))
            return

    last_start_command_time[user_id] = current_time

    os.environ['CHAT_ID'] =str(message.chat.id)
    print(f"User not logged in yet!{os.getenv('CHAT_ID')}")
    sent_msg = bot.send_message(message.chat.id, "\U00002b55 نام کاربری خود را وارد کنید:")
    bot.register_next_step_handler(sent_msg, username_handler)


def username_handler(message):

    global username

    username = message.text
    sent_msg = bot.send_message(message.chat.id, "\U00002b55 کلمه عبور خود را وارد کنید:")
    bot.register_next_step_handler(sent_msg, secure_handler)

    # Task to be scheduled.
def Task():
    global previous_issue_count
    global previous_issues
    session_token = authenticate_and_get_session(os.getenv('JIRA_USERNAME'), os.getenv('JIRA_PASSWORD'))
    if session_token:
        issues = get_issues(session_token)
        if issues:
            issue_count = len(issues)
            if issue_count > previous_issue_count:
                new_issues_count = issue_count - previous_issue_count
                message_text = f"تعداد تسک های باز شما در حال حاضر\U00002714 مورد\n: {new_issues_count}\n"
                for issue in issues:
                    if issue['key'] not in previous_issues:
                        issue_key = issue['key']
                        summary = issue['fields']['summary']
                        creator = issue['fields']['creator']['displayName']
                        message_text += f"\U000027a1 Issue Key: {issue_key}\n \U0001f300 Summary: {summary}\n \U0001f300 Creator: {creator}\n\n"
                        previous_issues[issue_key] = issue
                bot.send_message(os.getenv('CHAT_ID'), message_text)
                previous_issue_count = issue_count
            else:
                previous_issue_count = issue_count


# Handle the user's response to the password prompt.

def secure_handler(message):

    global secure

    secure =message.text
    hashed_secure = hashlib.sha256(secure.encode()).hexdigest()
    session_token = authenticate_and_get_session(username, secure)

    if session_token:
        bot.send_message(message.chat.id,f"{os.getenv('JIRA_USERNAME')} احراز هویت شما با موفقیت انجام شد.")


        issues = get_issues(session_token)
        if len(issues)==0:
            bot.send_message(message.chat.id, " \U0000203C برای شما Issue در وضعیت TO DO وجود ندارد ")
        else:
            bot.send_message(message.chat.id, " \U00002747 آخرین Issue های با وضعیت کلی TO DO برای شما")
            if issues:
                for issue in issues:
                    issue_key = issue['key']
                    summary = issue['fields']['summary']
                    creator = issue['fields']['creator']['displayName']
                    message_text = f"\U000027a1 Issue Key: {issue_key}\n \U0001f300 Summary: {summary}\n \U0001f300 Creator: {creator}"

                    bot.send_message(message.chat.id, message_text)
                    print(os.getenv('CHAT_ID'))



        schedule.every(1).minutes.do(Task)

        while True:
            schedule.run_pending()
            time.sleep(1)
    else:
        bot.send_message(message.chat.id, "\U0000203C کلمه عبور و یا نام کاربری خود را بدرستی وارد کرده\n و یا اتصال اینترنت خود را چک کنید\n در صورت اطمینان از عدم مشکل از سمت شما با پشتیبانی تماس بگیرید")


# handle other comment
@bot.message_handler(func=lambda message: True)
def echo_all(message):
	bot.reply_to(message, "\U00002734 لطفاً ابتدا دستور /start را ارسال کنید.")


bot.polling()
