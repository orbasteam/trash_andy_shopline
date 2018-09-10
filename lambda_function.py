# coding=utf-8
import boto3
import os
import logging
import urllib
import random

logger = logging.getLogger()
logger.setLevel(logging.INFO)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
SLACK_URL = "https://slack.com/api/chat.postMessage"
TABLE = "trash_andy_password"


def lambda_handler(data, context):

    try:
        slack_event = data['event']
        print(slack_event)

        if "bot_id" not in slack_event:

            text = slack_event.get('text')
            array_text = text.split()
            first_text = array_text[1]
            if first_text == '終極密碼':
                try:
                    min_number, max_number = array_text[2].split("-")
                    text = start_play_password(int(min_number), int(max_number))
                except IndexError:
                    pass
            elif is_number(first_text) and len(array_text) == 2:
                text = guess_password(int(first_text))

            post_message(text, slack_event["channel"])

    except Exception as e:
        print('error', str(e))

    return {
        "text": "已發送"
    }


def start_play_password(min_number, max_number):

    table = dynamodb().Table(TABLE)
    number = random.randrange(min_number, max_number)

    table.update_item(Key={"id": 1}, AttributeUpdates={
        "number": {"Value": number},
        "min": {"Value": min_number},
        "max": {"Value": max_number}
    })

    return '開始終極密碼遊戲 {} ~ {}'.format(min_number, max_number)


def guess_password(guess_number):
    try:

        print("guess number: " + str(guess_number))

        guess_number = int(guess_number)

        table = dynamodb().Table(TABLE)
        item = table.get_item(Key={"id": 1})['Item']

        number = int(item['number'])

        if int(item['min']) <= guess_number <= int(item['max']):
            if guess_number == number:
                table.delete_item(Key={"id": 1})
                return '碰！自爆，哈哈'
            elif guess_number > number:
                table.update_item(Key={"id": 1}, AttributeUpdates={"max": {"Value": guess_number}})
                return "{} ~ {}".format(item['min'], guess_number)
            else:
                table.update_item(Key={"id": 1}, AttributeUpdates={"min": {"Value": guess_number}})
                return "{} ~ {}".format(guess_number, item['max'])
        else:
            return '媽的，再亂猜，{} ~ {} 啦幹！'.format(item['min'], item['max'])

    except IndexError:
        return '終極密碼沒開始，猜個屁'


def post_message(word, channel_id):
    print(word, channel_id)
    data = urllib.parse.urlencode(
        (
            ("link_names", 1),
            ("token", BOT_TOKEN),
            ("channel", channel_id),
            ("text", word)
        )
    )
    data = data.encode("ascii")

    request = urllib.request.Request(
        SLACK_URL,
        data=data,
        method="POST"
    )

    request.add_header(
        "Content-Type",
        "application/x-www-form-urlencoded"
    )

    urllib.request.urlopen(request).read()


def is_number(value):
    try:
        int(value)
    except ValueError:
        return False

    return True


def dynamodb():
    session = boto3.session.Session()
    return session.resource('dynamodb')
