import os
import sys
import json
import random
import re
import requests
from flask import Flask, request

app = Flask(__name__)


@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing
    jokes = { 'stupid': ["""JS is so stupid, he needs a recipe to make ice cubes.""", 
                     """JS is so stupid, he thinks DNA is the National Dyslexics Association."""], 
         'fat':      ["""JS is so fat, when he goes to a restaurant, instead of a menu, he gets an estimate.""", 
                      """ JS is so fat, when the cops see him on a street corner, they yell, "Hey you guys, break it up!" """], 
         'dumb': ["""JS is so dumb, when God was giving out brains, he thought they were milkshakes and asked for extra thick.""", 
                  """JS is so dumb, he locked his keys inside his motorcycle."""] }

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = messaging_event["message"]["text"]  # the message's text

                    tokens = re.sub(r"[^a-zA-Z0-9\s]",' ',message_text).lower().split()
                    joke_text = ''
                    for token in tokens:
                        if token in jokes:
                            joke_text = random.choice(jokes[token])
                            break
                    if not joke_text:
                        joke_text = "I didn't understand! Send 'stupid', 'fat', 'dumb' for a JS joke!" 
                    user_details_url = "https://graph.facebook.com/v2.9/%s"%sender_id 
                    user_details_params = {'fields':'first_name,last_name,profile_pic', 'access_token':os.environ["PAGE_ACCESS_TOKEN"]} 
                    user_details = requests.get(user_details_url, user_details_params).json() 
                    joke_text = 'Hi '+user_details['first_name']+' '+user_details['last_name']+'..! ' + joke_text
                    send_message(sender_id, joke_text)

                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    pass

    return "ok", 200


def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)
