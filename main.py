import requests
from requests.auth import HTTPBasicAuth
import json
import telebot
from telebot.async_telebot import AsyncTeleBot
import asyncio
import hashlib
from telebot import types
import os
import schedule
import time


#telebot Token
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
os.environ['CHAT_ID'] = ''


headers = {
  "Accept": "application/json",
  "Content-Type": "application/json"
}

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
        "jql": f"assignee = {username}",
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

@bot.message_handler(commands=['start'])
def start_message(message):
    os.environ['CHAT_ID'] =str(message.chat.id)
    sent_msg = bot.send_message(message.chat.id, "نام کاربری خود را وارد کنید:")
    bot.register_next_step_handler(sent_msg, username_handler)

def username_handler(message):

    global username

    username = message.text
    sent_msg = bot.send_message(message.chat.id, "کلمه عبور را وارد کنید:")
    bot.register_next_step_handler(sent_msg, secure_handler)


def job():
    session_token = authenticate_and_get_session(os.getenv('JIRA_USERNAME'), os.getenv('JIRA_PASSWORD'))
    if session_token:
        issues = get_issues(session_token)
        if issues:
            for issue in issues:
                issue_key = issue['key']
                summary = issue['fields']['summary']
                creator = issue['fields']['creator']['displayName']
                message_text = f" Issue Key: {issue_key}\n Summary: {summary}\n Creator: {creator}"
                bot.send_message(os.getenv('CHAT_ID'), message_text)


def secure_handler(message):

    global secure

    secure = message.text
    hashed_secure = hashlib.sha256(secure.encode()).hexdigest()
    session_token = authenticate_and_get_session(username, secure)

    if session_token:
        bot.send_message(message.chat.id,f"احراز هویت با موفقیت انجام شد{os.getenv('JIRA_USERNAME')}.")
        issues = get_issues(session_token)


        if issues:
            for issue in issues:
                issue_key = issue['key']
                summary = issue['fields']['summary']
                creator = issue['fields']['creator']['displayName']
                message_text = f" Issue Key: {issue_key}\n Summary: {summary}\n Creator: {creator}"
                bot.send_message(message.chat.id, message_text)
                print(os.getenv('CHAT_ID'))

        schedule.every(1).minutes.do(job)

        while True:
            schedule.run_pending()
            time.sleep(1)




bot.polling()
