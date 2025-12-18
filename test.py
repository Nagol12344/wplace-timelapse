#!/usr/bin/env python3

import httplib2
import os
import random, json, typing
import sys
import time
import http.client

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

class Config:

    def __init__(self):
        self.verify_config()
        self.config = json.load(open("config.json"))

    def verify_config(self):
        config = json.load(open("config.json"))
        if (not config["interval"]) or config["interval"] < 1 or not isinstance(config["interval"], int):
            raise ValueError("Invalid interval.")
        if not config["imagesPerVideo"] or config["imagesPerVideo"] < 1 or not isinstance(config["imagesPerVideo"], int):
            raise ValueError("Invalid imagesPerVideo.")
        if not config["imageSaveDir"] or not isinstance(config["imageSaveDir"], str):
            raise ValueError("Invalid imageSaveDir.")
        if not config["videoSaveDir"] or not isinstance(config["videoSaveDir"], str):
            raise ValueError("Invalid videoSaveDir.")
        if not config["location"]["start"] or not len(config["location"]["start"]) == 4 or config["location"]["start"][0] < 1 or config["location"]["start"][1] < 1 or config["location"]["start"][2] < 1 or config["location"]["start"][3] < 1:
            print(config["location"]["start"])
            raise ValueError("Invalid location.start")
        if not config["location"]["end"] or not len(config["location"]["end"]) == 4 or config["location"]["end"][0] < 1 or config["location"]["end"][1] < 1 or config["location"]["end"][2] < 1 or config["location"]["end"][3] < 1:
            raise ValueError("Invalid location.end")
        if not config["webhookUrl"] or not isinstance(config["webhookUrl"], str):
            raise ValueError("Invalid webhookUrl.")
        if not config["playlistId"] or not isinstance(config["playlistId"], str):
            raise ValueError("Invalid playlistId.")

            # Getters for all config values
    def get_interval(self) -> int:
        return self.config["interval"]

    def get_images_per_video(self) -> int:
        return self.config["imagesPerVideo"]

    def get_image_save_dir(self) -> str:
        return self.config["imageSaveDir"]

    def get_video_save_dir(self) -> str:
        return self.config["videoSaveDir"]

    def get_location_start(self) -> typing.List[int]:
        return self.config["location"]["start"]

    def get_location_end(self) -> typing.List[int]:
        return self.config["location"]["end"]

    def get_webhook_url(self) -> str:
        return self.config["webhookUrl"]

    def get_playlist_id(self) -> str:
        return self.config["playlistId"]    

config = Config()
httplib2.RETRIES = 1

MAX_RETRIES = 10

RETRIABLE_EXCEPTIONS = (
    httplib2.HttpLib2Error,
    IOError,
    http.client.NotConnected,
    http.client.IncompleteRead,
    http.client.ImproperConnectionState,
    http.client.CannotSendRequest,
    http.client.CannotSendHeader,
    http.client.ResponseNotReady,
    http.client.BadStatusLine,
)

RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

CLIENT_SECRETS_FILE = "client_secrets.json"

YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

MISSING_CLIENT_SECRETS_MESSAGE = f"""
WARNING: Please configure OAuth 2.0

Populate the client_secrets.json file located at:

   {os.path.abspath(os.path.join(os.path.dirname(__file__), CLIENT_SECRETS_FILE))}

with information from:
https://console.cloud.google.com/
"""

VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")

def get_authenticated_service(args):
    flow = flow_from_clientsecrets(
      CLIENT_SECRETS_FILE,
      scope=[YOUTUBE_UPLOAD_SCOPE, "https://www.googleapis.com/auth/youtube.force-ssl"],
      message=MISSING_CLIENT_SECRETS_MESSAGE,
    )

    storage = Storage(f"upload_video.py-oauth2.json")
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, args)

    return build(
        YOUTUBE_API_SERVICE_NAME,
        YOUTUBE_API_VERSION,
        http=credentials.authorize(httplib2.Http()),
    )

def add_video_to_playlist(youtube, video_id, playlist_id):
    request = youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": "nbo3YPe2hSQ",
                }
            }
        }
    )
    response = request.execute()
    return response

args = 0 # dude idk im cheating this part
youtube = get_authenticated_service(args)
add_video_to_playlist(youtube, "video_id", config.get_playlist_id())