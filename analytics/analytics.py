__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


import os

import harperdb
import matplotlib.pyplot as plt

from all_nodes import constants
from all_nodes import utils


LOGGER = utils.get_logger(__name__)

HARPERDB_URL = "https://general-jaimervq.harperdbcloud.com/"
HARPERDB_READ_USERNAME = "HARPERDB_READ_USER"
HARPERDB_READ_PASSWORD = "k;J4^IhcKnTg}{"
HARPERDB_READ_AND_WRITE_USERNAME = "HARPERDB_READ_AND_WRITE_USER"
HARPERDB_READ_AND_WRITE_PASSWORD = os.getenv("HARPERDB_READ_AND_WRITE_PASSWORD")

ALL_NODES_SCHEMA = "all_nodes"
ENVIRONMENT = constants.HARPERDB_ENV
ALL_NODES_TABLE = f"node_usage_{ENVIRONMENT}"


def make_query(query_str: str):
    """Make a query to the DB

    Args:
        query_str (str): SQL query to be made

    Returns:
        list: list of entries
    """
    db = harperdb.HarperDB(
        url=HARPERDB_URL,
        username=HARPERDB_READ_USERNAME,
        password=HARPERDB_READ_PASSWORD,
    )

    return db.sql(query_str)


def submit_bulk_analytics(node_attrs_list):
    """Submit a series of records to DB

    Args:
        node_attrs_list (list): list of dicts to be submitted to DB
    """
    if not HARPERDB_READ_AND_WRITE_PASSWORD:
        LOGGER.info("Cannot submit the stats of this run to the DB")
        return

    LOGGER.info("Submitting stats...")
    db = harperdb.HarperDB(
        url=HARPERDB_URL,
        username=HARPERDB_READ_AND_WRITE_USERNAME,
        password=HARPERDB_READ_AND_WRITE_PASSWORD,
    )

    db.insert(ALL_NODES_SCHEMA, ALL_NODES_TABLE, node_attrs_list)
    LOGGER.info(
        f"Submitted {len(node_attrs_list)} entries to {ALL_NODES_SCHEMA}.{ALL_NODES_TABLE}"
    )


def process_analytics():
    """
    Create graphs with some node usage analytics
    """
    # Connecting to DB
    db = harperdb.HarperDB(
        url=HARPERDB_URL,
        username=HARPERDB_READ_USERNAME,
        password=HARPERDB_READ_PASSWORD,
    )

    LOGGER.info(f"Getting statistics from {ALL_NODES_SCHEMA}.{ALL_NODES_TABLE}")

    # Folder
    root = os.path.abspath(__file__)
    root_dir_path = os.path.dirname(root)
    os.makedirs(os.path.join(root_dir_path, "../docs/analytics"), exist_ok=True)

    # Style for plots
    plt.style.use("seaborn-v0_8-dark")

    # Overall usage
    res = db.sql(
        f"SELECT run_date, COUNT(*) as total "
        f"FROM {ALL_NODES_SCHEMA}.{ALL_NODES_TABLE} "
        f"WHERE run_date IS NOT NULL "
        f"GROUP BY run_date "
        f"ORDER BY run_date ASC "
        f"LIMIT 50"
    )

    if res:
        dates = list()
        uses = list()

        for r in res:
            dates.append(r.get("run_date"))
            uses.append(r.get("total"))

        fig, ax = plt.subplots(figsize=(10, 7))
        ax.plot(dates, uses)
        for tick in ax.get_xticklabels():
            tick.set_rotation(45)
            tick.set_horizontalalignment("right")
        ax.set_ylabel("Amount of nodes run")
        ax.set_title(f"Recent usage")

        graph_file = os.path.join(
            root_dir_path, "../docs/analytics", "recent_usage.png"
        )
        fig.tight_layout()
        fig.savefig(graph_file)

    # Most used
    res = db.sql(
        f"SELECT COUNT(id) AS total, class_name "
        f"FROM {ALL_NODES_SCHEMA}.{ALL_NODES_TABLE} "
        f"WHERE class_name NOT LIKE '%Input' AND class_name NOT LIKE '%Ctx' AND NOT IS_CONTEXT "
        f"GROUP BY class_name "
        f"ORDER BY total DESC "
        f"LIMIT 30"
    )

    if res:
        node_names = list()
        uses = list()

        for r in res:
            node_names.append(r.get("class_name"))
            uses.append(r.get("total"))

        fig, ax = plt.subplots(figsize=(10, 7))
        ax.barh(node_names, uses)
        ax.set_xlabel("Number of usages")
        ax.set_ylabel("Node class")
        ax.invert_yaxis()
        ax.set_title(f"Top 30 most used nodes")

        graph_file = os.path.join(root_dir_path, "../docs/analytics", "most_used.png")
        fig.tight_layout()
        fig.savefig(graph_file)

    # Exec times
    res = db.sql(
        f"SELECT AVG(execution_time) AS average_time, class_name "
        f"FROM {ALL_NODES_SCHEMA}.{ALL_NODES_TABLE} "
        f"WHERE NOT IS_CONTEXT "
        f"AND class_name != 'TimedNode' "
        f"AND class_name != 'StartFile' "
        f"GROUP BY class_name "
        f"ORDER BY average_time DESC "
        f"LIMIT 10"
    )

    if res:
        node_names = list()
        avg_time = list()

        for r in res:
            node_names.append(r.get("class_name"))
            avg_time.append(r.get("average_time"))

        fig, ax = plt.subplots(figsize=(10, 7))
        ax.barh(node_names, avg_time)
        ax.set_xlabel("Average execution time (s)")
        ax.set_ylabel("Node class")
        ax.invert_yaxis()
        ax.set_title(f"Top 10 slowest nodes")

        graph_file = os.path.join(root_dir_path, "../docs/analytics", "slowest.png")
        fig.tight_layout()
        fig.savefig(graph_file)

    # Last errored
    res = db.sql(
        f"SELECT class_name, run_date "
        f"FROM {ALL_NODES_SCHEMA}.{ALL_NODES_TABLE} "
        f"WHERE success='ERROR' "
        f"ORDER BY run_date ASC "
        f"LIMIT 50"
    )

    if res:
        node_names = list()
        error_date = list()

        for r in res:
            node_names.append(r.get("class_name"))
            error_date.append(r.get("run_date")[:10])

        fig, ax = plt.subplots(figsize=(10, 7))
        ax.scatter(error_date, node_names, c="red", alpha=0.3, s=60, edgecolors="black")
        ax.set_xlabel("Error date")
        for tick in ax.get_xticklabels():
            tick.set_rotation(45)
            tick.set_horizontalalignment("right")
        ax.set_ylabel("Node class")
        ax.set_title(f"Most recently errored nodes")
        ax.grid(which="major", axis="x", linestyle="--")

        graph_file = os.path.join(root_dir_path, "../docs/analytics", "errored.png")
        fig.tight_layout()
        fig.savefig(graph_file)

    # Last failed
    res = db.sql(
        f"SELECT class_name, run_date "
        f"FROM {ALL_NODES_SCHEMA}.{ALL_NODES_TABLE} "
        f"WHERE success='FAILED' "
        f"ORDER BY run_date ASC "
        f"LIMIT 50"
    )

    if res:
        node_names = list()
        failed_date = list()

        for r in res:
            node_names.append(r.get("class_name"))
            failed_date.append(r.get("run_date")[:10])

        fig, ax = plt.subplots(figsize=(10, 7))
        ax.scatter(
            failed_date, node_names, c="orange", alpha=0.3, s=60, edgecolors="black"
        )
        ax.set_xlabel("Failure date")
        for tick in ax.get_xticklabels():
            tick.set_rotation(45)
            tick.set_horizontalalignment("right")
        ax.set_ylabel("Node class")
        ax.set_title(f"Most recently failed nodes")
        ax.grid(which="major", axis="x", linestyle="--")

        graph_file = os.path.join(root_dir_path, "../docs/analytics", "failed.png")
        fig.tight_layout()
        fig.savefig(graph_file)

    LOGGER.info(f"Processed statistics from {ALL_NODES_SCHEMA}.{ALL_NODES_TABLE}")
