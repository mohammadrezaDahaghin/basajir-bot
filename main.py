import requests
from requests.auth import HTTPBasicAuth
import json
import telebot
from telebot.async_telebot import AsyncTeleBot
import asyncio
import hashlib
from telebot import types
import os
TOKEN ="6463346745:AAGtSlb2baBQSWF7dwT-xnj4sksE9ApOwxc"
bot = telebot.TeleBot(TOKEN)

# Jira base URL
base_url = 'https://jira.basa.ir'

# Authentication endpoint
auth_url = f'{base_url}/jira/rest/auth/1/session'
getissue_url = f'{base_url}/jira/rest/api/2/search'

os.environ['SESSION_VALUE'] = ''
os.environ['JIRA_USERNAME'] = ''
os.environ['JIRA_PASSWORD'] = ''


headers = {
  "Accept": "application/json",
  "Content-Type": "application/json"
}

def authenticate_and_get_session(username, password):
    data = {"username": username, "password": password}
    print(username)
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
    # us=os.getenv('JIRA_USERNAME')
    sessio = session_value
    print(f'assignee = {username}{session_value}')

    # params = {"jql": f"assignee = {username}", "maxResults": 1}
    payload = json.dumps({
        "jql": f"assignee = {username}",
        "maxResults": 1
    })
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {session_value}"
    }
    print(getissue_url)
    response = requests.post(getissue_url, data=payload, headers=headers)
    print(response.json())
    if response.status_code == 200:
        print("1")
        return response.json().get('issues', [])
    else:
        print("2")
        return None

@bot.message_handler(commands=['start'])
def start_message(message):
    sent_msg = bot.send_message(message.chat.id, "نام کاربری خود را وارد کنید:")
    bot.register_next_step_handler(sent_msg, username_handler)

def username_handler(message):
    global username
    username = message.text
    sent_msg = bot.send_message(message.chat.id, "کلمه عبور را وارد کنید:")
    bot.register_next_step_handler(sent_msg, secure_handler)

def secure_handler(message):

    global secure
    secure = message.text
    hashed_secure = hashlib.sha256(secure.encode()).hexdigest()
    session_token = authenticate_and_get_session(username, secure)
    print(f"se--{session_token}")
    if session_token:
        bot.send_message(message.chat.id,f"احراز هویت با موفقیت انجام شد.{os.getenv('JIRA_USERNAME')}")
        # print(usernameme)
        issues = get_issues(session_token)
        print(issues)


        if issues:
            for issue in issues:
                issue_key = issue['key']
                summary = issue['fields']['summary']
                creator = issue['fields']['creator']['displayName']
                message_text = f"Issue Key: {issue_key}\nSummary: {summary}\nCreator: {creator}"
                print(message_text)
                bot.send_message(message.chat.id, message_text)

bot.polling()
