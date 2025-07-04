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
        LOGGER.debug(f"Sent: {resp.status_code}")


class DownloadToTxt(GeneralLogicNode):
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
