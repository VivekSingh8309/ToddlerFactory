import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


class YouTubeUploader:

    def __init__(self):
        self.youtube = self.authenticate()

    def authenticate(self):
        creds = None

        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file(
                "token.json",
                SCOPES
            )

        if not creds or not creds.valid:

            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())

            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "client_secret.json",
                    SCOPES
                )

                creds = flow.run_local_server(port=0)

            with open("token.json", "w") as token:
                token.write(creds.to_json())

        return build(
            "youtube",
            "v3",
            credentials=creds
        )

    def upload(
        self,
        video_path,
        title,
        description="",
        tags=None,
        privacy="private"
    ):

        request = self.youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags or [],
                    "categoryId": "1"
                },
                "status": {
                    "privacyStatus": privacy,
                    "selfDeclaredMadeForKids": True
                }
            },
            media_body=MediaFileUpload(
                video_path,
                chunksize=-1,
                resumable=True
            ),
        )

        response = None

        while response is None:
            status, response = request.next_chunk()

            if status:
                print(
                    f"Uploading... {int(status.progress()*100)}%"
                )

        print("Upload complete!")

        return response["id"]