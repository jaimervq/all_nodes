__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


class SendPushNotification(GeneralLogicNode):
    INPUTS_DICT = {
        "title": {"type": str},
        "body": {"type": str},
    }

    OUTPUTS_DICT = {"status_code": {"type": int, "optional": True}}

    def run(self):
        import os
        import requests

        api_key = os.getenv("PUSHBULLET_TOKEN")
        if api_key is None:
            LOGGER.warning("PUSHBULLET_TOKEN is not set, cannot send you notifications")
            return

        title = self.get_input("title")
        body = self.get_input("body")

        data = {"type": "note", "title": title, "body": body}
        resp = requests.post(
            "https://api.pushbullet.com/v2/pushes",
            json=data,
            headers={"Access-Token": api_key},
        )
        self.set_output("status_code", resp.status_code)


class DownloadToTextFile(GeneralLogicNode):
    INPUTS_DICT = {
        "url": {"type": str},
        "filename": {"type": str},
    }

    def run(self):
        import requests

        url = self.get_input("url")
        filename = self.get_input("filename")

        response = requests.get(url)

        if response.status_code == 200:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(response.text)
            LOGGER.info(f"Downloaded and saved as '{filename}'")
        else:
            self.fail(f"Failed to download. Status code: {response.status_code}")


class DownloadImage(GeneralLogicNode):
    INPUTS_DICT = {
        "url": {"type": str},
        "filename": {"type": str},
    }

    OUTPUTS_DICT = {"status_code": {"type": int, "optional": True}}

    def run(self):
        import requests

        url = self.get_input("url")
        filename = self.get_input("filename")

        response = requests.get(url)

        self.set_output("status_code", response.status_code)

        if response.status_code == 200:
            with open(filename, "wb") as f:
                f.write(response.content)
            LOGGER.info(f"Downloaded and saved as '{filename}'")
        else:
            self.fail(f"Failed to download. Status code: {response.status_code}")


class DownloadMultipleImages(GeneralLogicNode):
    INPUTS_DICT = {
        "urls": {"type": list},
        "folder_path": {"type": str},
    }

    def run(self):
        from all_nodes.helpers.rust import rust_requests

        urls = self.get_input("urls")
        folder_path = self.get_input("folder_path")

        rust_requests.download_images(urls, folder_path)
