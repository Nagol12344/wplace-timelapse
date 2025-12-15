import json
import downloader
import os, sys
import typing
import ffmpeg
import datetime
import time
import requests


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


def send_webhook(webhook_url: str):
    if webhook_url == "":
        return
    data = {
        "embeds": [
            {
                "title": "Video generated",
                "description": "Next video created!",
            }
        ],
        "attachments": []
    }
    try:
        response = requests.post(webhook_url, json=data)
        if response.status_code != 204 and response.status_code != 200:
            print(
                f"Failed to send webhook: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Exception occurred while sending webhook: {e}")

def run_timelapse_parser(lastImage: int, config: Config, sleep: bool=False):
    lastImage += 1
    print(f"Downloading image {lastImage}")
    try:
        downloader.download_image(
            tuple(config.get_location_start()),
            tuple(config.get_location_end()),
            return_image=True
        ).save(f"{config.get_image_save_dir()}/{lastImage:05}.png")
    except Exception as e:
        print(f"Error downloading image: {e}")
        lastImage -= 1
        time.sleep(10)
        raise Exception("whoops")
    if lastImage % config.get_images_per_video() == 0:
        print("Creating timelapse video")
        (
            ffmpeg
            .input(f"{config.get_image_save_dir()}/%05d.png", framerate=15)
            # ensure even dimensions
            .filter('scale', 'trunc(iw/2)*2', 'trunc(ih/2)*2')
            .output(f"{config.get_video_save_dir()}/timelapse_{datetime.date.today().isoformat()}_{datetime.datetime.now().time()}.mp4", vcodec="libx264", pix_fmt="yuv420p")
            .run(overwrite_output=True)
        )
        # delete all the images if the video was created successfully
        directory = os.listdir(config.get_image_save_dir())
        for file in directory:
            os.remove(f"{config.get_image_save_dir()}/{file}")
        lastImage = 0
        send_webhook(config.get_webhook_url())
    if sleep:
        time.sleep(config.get_interval())

def main():
    config = Config()
    lastImage = 0
    if os.path.exists(config.get_image_save_dir()):
        directory = os.listdir(config.get_image_save_dir())
        for file in directory:
            filenumber = int(file.split(".")[0])
            if filenumber > lastImage:
                lastImage = filenumber
    os.makedirs(config.get_image_save_dir(), exist_ok=True)
    os.makedirs(config.get_video_save_dir(), exist_ok=True)
    try:
        if sys.argv[1] == "--cron": 
            try: 
                run_timelapse_parser(lastImage, config, sleep=False)
            except:
                run_timelapse_parser(lastImage, config, sleep=False)
            exit()
    except IndexError: # there is no way there isnt a better way to solve this problem I just don't care to find it
        pass
    while True:
        try: 
            run_timelapse_parser(lastImage, config, sleep=True)
        except:
            run_timelapse_parser(lastImage, config, sleep=True)


if __name__ == "__main__":
    main()
