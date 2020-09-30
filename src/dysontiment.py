from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from google.cloud import pubsub_v1
from google.oauth2 import service_account
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types
import google.cloud.logging as gcl
from google.cloud.logging.handlers import CloudLoggingHandler
import googlemaps
import configparser
import logging
import json
import os
from datetime import datetime
from src.cloud_secrets_helper import CloudSecretsHelper


class Listener(StreamListener):
    def on_data(self, data):
        json_data = json.loads(data)

        tweet_text = json_data['text']
        tweet_lang = json_data['lang']
        tweet_sent = analyse_sentiment(tweet_text, tweet_lang)
        if tweet_sent is None:
            return
        tweet_loc = place_search(json_data['user']['location'], tweet_lang)
        dtime = json_data['created_at']
        tweet_dt = datetime.strftime(datetime.strptime(dtime, '%a %b %d %H:%M:%S +0000 %Y'), '%Y-%m-%d %H:%M:%S')

        cleaned_data = {
            "id": json_data['id_str'],
            "created_at": tweet_dt,
            "user_location": tweet_loc,
            "text": tweet_text,
            "sentiment": tweet_sent
        }
        try:
            pubsub_client.publish(topic_path, data=json.dumps(cleaned_data).encode('utf-8'))
            logging.info("Successfully published tweet data")
        except:
            logging.error("Tweet could not be published to topic | {}".format(cleaned_data))

    def on_error(self, status):
        logging.error("Tweet could not be retrieved | {}".format(status))


def analyse_sentiment(tweet_text, lang):
    document = types.Document(
        content=tweet_text,
        language=lang,
        type=enums.Document.Type.PLAIN_TEXT)
    try:
        annotations = lang_client.analyze_sentiment(document=document)
    except:
        logging.error("Sentiment analysis failed | {} | {}".format(tweet_text, lang))
        return None

    if annotations.document_sentiment.magnitude < 0.1:
        logging.info("Sentiment confidence too low | {}".format(annotations.document_sentiment.magnitude))
        return None
    return annotations.document_sentiment.score


def place_search(query, lang):
    if query is None:
        logging.info("No user location, skipping place search")
        return None
    try:
        loc = gmaps.find_place(query,
                               "textquery",
                               fields=["geometry/location"],
                               language=lang)
    except:
        logging.error("User location retrieval failed | {}".format(query))
        return None
    if loc['status'] != 'OK':
        logging.info("User location could not be found | {}".format(query))
        return None
    wkt_loc = "POINT({} {})".format(loc['candidates'][0]['geometry']['location']['lng'], loc['candidates'][0]['geometry']['location']['lat'])
    logging.info("User location successfully found | {}".format(query))
    return wkt_loc


config = configparser.ConfigParser()
config.read("config.conf")
PROJECT_NAME = config["Config"]["PROJECT_NAME"]

in_cloud = os.environ.get('AM_I_IN_A_DOCKER_CONTAINER', False)
if in_cloud:
    pubsub_client = pubsub_v1.PublisherClient()
    lang_client = language.LanguageServiceClient()
    secrets = CloudSecretsHelper(PROJECT_NAME)

    logging.debug('Detected running on Google Cloud')
    client = gcl.Client()
    client.setup_logging()
    handler = CloudLoggingHandler(client)
    cloud_logger = logging.getLogger('cloudLogger')
    cloud_logger.setLevel(logging.DEBUG)
    cloud_logger.addHandler(handler)
else:
    credentials = service_account.Credentials.from_service_account_file(config["Auth"]["AUTH_FILE_PATH"])
    pubsub_client = pubsub_v1.PublisherClient(credentials=credentials)
    lang_client = language.LanguageServiceClient(credentials=credentials)
    secrets = CloudSecretsHelper(PROJECT_NAME, credentials=credentials)
    logging.basicConfig(level=logging.INFO)

topic_path = pubsub_client.topic_path(PROJECT_NAME, config["Config"]["PUBSUB_TOPIC"])

consumer_key = secrets.get_secret(config["Auth"]["CONSUMER_KEY_PATH"])
consumer_secret = secrets.get_secret(config["Auth"]["CONSUMER_SECRET_PATH"])
access_token = secrets.get_secret(config["Auth"]["ACCESS_TOKEN_PATH"])
access_token_secret = secrets.get_secret(config["Auth"]["ACCESS_TOKEN_SECRET_PATH"])
maps_api_key = secrets.get_secret(config["Auth"]["MAPS_API_KEY_PATH"])

try:
    gmaps = googlemaps.Client(key=maps_api_key)
except Exception as e:
    logging.critical("Google maps client setup failed")
    logging.critical(e)
    raise e

tracklist = config['Config']['TRACKLIST']
tracklist = tracklist.split(',')

l = Listener()
auth = OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
stream = Stream(auth, l)
stream.filter(track=tracklist)
