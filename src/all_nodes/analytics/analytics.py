__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


import os
import re

import matplotlib.pyplot as plt
import polars as pl
from pymongo import MongoClient

from all_nodes import constants
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


DB_READ_AND_WRITE_PASSWORD = os.getenv("DB_READ_AND_WRITE_PASSWORD")
DB_USERNAME = "jaimervq" if DB_READ_AND_WRITE_PASSWORD else "readonly_user"
DB_PASSWORD = DB_READ_AND_WRITE_PASSWORD or "BqrWK1TzOmLfcqq2"
CONNECTION_STRING = f"mongodb+srv://{DB_USERNAME}:{DB_PASSWORD}@cluster0.rud2hei.mongodb.net/?retryWrites=true&w=majority"

ENVIRONMENT = constants.DB_ENV
ALL_NODES_DB = "all_nodes"
ALL_NODES_TABLE = f"node_usage_{ENVIRONMENT}"


# -------------------------------- CLIENT -------------------------------- #
mongo_client = None
try:
    mongo_client = MongoClient(CONNECTION_STRING)
    LOGGER.debug(mongo_client.admin.command("ping"))
    LOGGER.info(f"Connected to MongoDB for analytics, username: {DB_USERNAME}")
except Exception:
    LOGGER.info("No statistics will be submitted!")


# -------------------------------- METHODS -------------------------------- #
def get_collection():
    db = mongo_client[ALL_NODES_DB]
    return db[ALL_NODES_TABLE]


def make_query(query_dict: dict):
    """Make a query to the DB

    Args:
        query_str (dict): query to be made

    Returns:
        pymongo.cursor.Cursor
    """
    table = get_collection()
    return table.find(query_dict)


def make_query_aggregation(pipeline: list):
    """Make a query to the DB

    Args:
        pipeline (list): pipeline for query

    Returns:
        pymongo.cursor.Cursor
    """
    table = get_collection()
    return table.aggregate(pipeline)


def submit_bulk_analytics(node_attrs_list):
    """Submit a series of records to DB

    Args:
        node_attrs_list (list): list of dicts to be submitted to DB
    """
    if not DB_READ_AND_WRITE_PASSWORD:
        LOGGER.info("Cannot submit the stats of this run to the DB")
        return

    if not node_attrs_list:
        LOGGER.info("Nothing to submit")
        return

    table = get_collection()
    LOGGER.info(f"Submitting stats to {ALL_NODES_DB}.{ALL_NODES_TABLE}...")
    table.insert_many(node_attrs_list)


def process_analytics():
    """
    Create graphs with some node usage analytics
    """
    LOGGER.info(f"Getting statistics from {ALL_NODES_DB}.{ALL_NODES_TABLE}")

    # Folder
    root = os.path.abspath(__file__)
    root_dir_path = os.path.dirname(root)
    os.makedirs(os.path.join(root_dir_path, "../../../docs/analytics"), exist_ok=True)

    # Style for plots
    plt.style.use("seaborn-v0_8-dark")

    # Overall usage ---------------------------------------
    res = make_query_aggregation(
        [
            {"$match": {"run_date": {"$ne": None}}},
            {"$group": {"_id": "$run_date", "count": {"$sum": 1}}},
            {"$sort": {"_id": 1}},
            {"$limit": 35},
        ]
    )

    if res:
        df = pl.DataFrame(list(res))

        dates = df["_id"].to_list()
        uses = df["count"].to_list()

        fig, ax = plt.subplots(figsize=(10, 7))
        ax.plot(dates, uses)
        for tick in ax.get_xticklabels():
            tick.set_rotation(45)
            tick.set_horizontalalignment("right")
            tick.set_fontsize(9)
        ax.set_ylabel("Amount of nodes run")
        ax.set_title("Recent usage")

        graph_file = os.path.join(
            root_dir_path, "../../../docs/analytics", "recent_usage.png"
        )
        fig.tight_layout()
        fig.savefig(graph_file)

    # Most used ---------------------------------------
    res = make_query_aggregation(
        [
            {
                "$match": {
                    "$nor": [
                        {"class_name": re.compile(".*Input")},
                        {"class_name": re.compile(".*Ctx")},
                    ],
                    "IS_CONTEXT": {"$ne": True},
                }
            },
            {"$group": {"_id": "$class_name", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 30},
        ]
    )

    if res:
        df = pl.DataFrame(list(res))

        node_names = df["_id"].to_list()
        uses = df["count"].to_list()

        fig, ax = plt.subplots(figsize=(10, 7))
        ax.barh(node_names, uses)
        ax.set_xlabel("Number of usages")
        ax.set_ylabel("Node class")
        ax.invert_yaxis()
        ax.set_title("Top 30 most used nodes")

        graph_file = os.path.join(
            root_dir_path, "../../../docs/analytics", "most_used.png"
        )
        fig.tight_layout()
        fig.savefig(graph_file)

    # Last errored ---------------------------------------
    res = make_query_aggregation(
        [
            {
                "$match": {
                    "success": {"$eq": "ERROR"},
                    "run_date": {"$ne": None},
                }
            },
            {"$sort": {"run_date": 1}},
            {"$limit": 50},
        ]
    )

    if res:
        df = pl.DataFrame(list(res))

        df_grouped = df.group_by(
            ["class_name", "run_date"], maintain_order=True
        ).count()

        node_names = df_grouped["class_name"].to_list()
        failed_date = df_grouped["run_date"].to_list()
        occurrences = df_grouped["count"].to_list()

        fig, ax = plt.subplots(figsize=(10, 7))
        ax.scatter(
            failed_date,
            node_names,
            c="red",
            alpha=0.5,
            s=[min(5000, 30 * o) for o in occurrences],
            edgecolors="black",
        )
        ax.set_xlabel("Error date")
        for tick in ax.get_xticklabels():
            tick.set_rotation(45)
            tick.set_horizontalalignment("right")
        ax.set_ylabel("Node class")
        ax.set_title("Most recently errored nodes")
        ax.grid(which="major", axis="x", linestyle="--")

        graph_file = os.path.join(
            root_dir_path, "../../../docs/analytics", "errored.png"
        )
        fig.tight_layout()
        fig.savefig(graph_file)

    # Last failed ---------------------------------------
    res = make_query_aggregation(
        [
            {
                "$match": {
                    "success": {"$eq": "FAILED"},
                    "run_date": {"$ne": None},
                }
            },
            {"$sort": {"run_date": 1}},
            {"$limit": 50},
        ]
    )

    if res:
        df = pl.DataFrame(list(res))

        df_grouped = df.group_by(
            ["class_name", "run_date"], maintain_order=True
        ).count()

        node_names = df_grouped["class_name"].to_list()
        failed_date = df_grouped["run_date"].to_list()
        occurrences = df_grouped["count"].to_list()

        fig, ax = plt.subplots(figsize=(10, 7))
        ax.scatter(
            failed_date,
            node_names,
            c="orange",
            alpha=0.5,
            s=[min(5000, 30 * o) for o in occurrences],
            edgecolors="black",
        )
        ax.set_xlabel("Failure date")
        for tick in ax.get_xticklabels():
            tick.set_rotation(45)
            tick.set_horizontalalignment("right")
        ax.set_ylabel("Node class")
        ax.set_title("Most recently failed nodes")
        ax.grid(which="major", axis="x", linestyle="--")

        graph_file = os.path.join(
            root_dir_path, "../../../docs/analytics", "failed.png"
        )
        fig.tight_layout()
        fig.savefig(graph_file)

    LOGGER.info(f"Processed statistics from {ALL_NODES_DB}.{ALL_NODES_TABLE}")
