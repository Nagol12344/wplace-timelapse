#!/usr/bin/env python3

import httplib2
import os
import random
import sys
import time
import http.client

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow


# Disable automatic retries; we handle retries manually
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

    storage = Storage(f"{sys.argv[0]}-oauth2.json")
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run_flow(flow, storage, args)

    return build(
        YOUTUBE_API_SERVICE_NAME,
        YOUTUBE_API_VERSION,
        http=credentials.authorize(httplib2.Http()),
    )


def initialize_upload(youtube, options):
    tags = options.keywords.split(",") if options.keywords else None

    body = {
        "snippet": {
            "title": options.title,
            "description": options.description,
            "tags": tags,
            "categoryId": options.category,
        },
        "status": {
            "privacyStatus": options.privacyStatus,
        },
    }

    insert_request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=MediaFileUpload(
            options.file,
            chunksize=-1,
            resumable=True,
        ),
    )

    resumable_upload(insert_request)


def resumable_upload(insert_request):
    response = None
    error = None
    retry = 0

    while response is None:
        try:
            print("Uploading file...")
            status, response = insert_request.next_chunk()

            if response is not None:
                if "id" in response:
                    print(f"VIDEO_ID={response['id']}")
                else:
                    sys.exit(f"Unexpected response: {response}")

        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = f"Retriable HTTP error {e.resp.status}: {e.content}"
            else:
                raise

        except RETRIABLE_EXCEPTIONS as e:
            error = f"Retriable error occurred: {e}"

        if error:
            print(error)
            retry += 1
            if retry > MAX_RETRIES:
                sys.exit("Max retries exceeded.")

            sleep_seconds = random.random() * (2 ** retry)
            print(f"Sleeping {sleep_seconds:.2f} seconds before retry...")
            time.sleep(sleep_seconds)


if __name__ == "__main__":
    argparser.add_argument("--file", required=True, help="Video file to upload")
    argparser.add_argument("--title", default="Test Title")
    argparser.add_argument("--description", default="Test Description")
    argparser.add_argument("--category", default="22")
    argparser.add_argument("--keywords", default="")
    argparser.add_argument(
        "--privacyStatus",
        choices=VALID_PRIVACY_STATUSES,
        default="public",
    )

    args = argparser.parse_args()

    if not os.path.exists(args.file):
        sys.exit("Invalid --file path")

    youtube = get_authenticated_service(args)

    try:
        initialize_upload(youtube, args)
    except HttpError as e:
        print(f"HTTP error {e.resp.status}: {e.content}")
