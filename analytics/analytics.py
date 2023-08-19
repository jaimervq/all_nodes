__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


import os

import harperdb
from prettytable import PrettyTable

from all_nodes import constants
from all_nodes import utils

LOGGER = utils.get_logger(__name__)

HARPERDB_URL = "https://general-jaimervq.harperdbcloud.com/"
HARPERDB_READ_USERNAME = "READ_USER"
HARPERDB_READ_PASSWORD = "D2qrS2RdG@ycm&fz"
HARPERDB_READ_AND_WRITE_USERNAME = "READ_AND_WRITE_USER"
HARPERDB_READ_AND_WRITE_PASSWORD = os.getenv("HARPERDB_READ_AND_WRITE_PASSWORD")

ALL_NODES_SCHEMA="all_nodes"
ENVIRONMENT = "PROD" if not constants.IN_DEV else "DEV"
ALL_NODES_TABLE=f"node_usage_{ENVIRONMENT}"


def submit_bulk_analytics(node_attrs_list):
    if not HARPERDB_READ_AND_WRITE_PASSWORD:
        LOGGER.info("Cannot submit the stats of this run to the DB")
        return

    LOGGER.info("Submitting stats...")
    db = harperdb.HarperDB(
        url=HARPERDB_URL,
        username=HARPERDB_READ_AND_WRITE_USERNAME,
        password=HARPERDB_READ_AND_WRITE_PASSWORD)

    db.insert(ALL_NODES_SCHEMA, ALL_NODES_TABLE, node_attrs_list)
    LOGGER.info(f"Submitted {len(node_attrs_list)} entries to {ALL_NODES_SCHEMA}.{ALL_NODES_TABLE}")

def print_analytics_to_screen():
    db = harperdb.HarperDB(
        url=HARPERDB_URL,
        username=HARPERDB_READ_USERNAME,
        password=HARPERDB_READ_PASSWORD)

    # Most used
    res = db.sql(f"SELECT COUNT(id) AS total, class_name "
                 f"FROM {ALL_NODES_SCHEMA}.{ALL_NODES_TABLE} "
                 f"WHERE class_name NOT LIKE '%Input' AND NOT IS_CONTEXT "
                 f"GROUP BY class_name "
                 f"ORDER BY total DESC "
                 f"LIMIT 25")

    if res:
        top_used_table = PrettyTable()
        top_used_table.field_names = list(res[0].keys())
        for r in res:
            top_used_table.add_row(r.values())
        print("\nTOP 25 MOST USED CLASSES")
        print(top_used_table)

    # Exec times
    res = db.sql(f"SELECT AVG(execution_time) AS average_time, class_name "
                 f"FROM {ALL_NODES_SCHEMA}.{ALL_NODES_TABLE} "
                 f"WHERE NOT IS_CONTEXT "
                 f"GROUP BY class_name "
                 f"ORDER BY average_time DESC "
                 f"LIMIT 10")

    if res:
        slowest_table = PrettyTable()
        slowest_table.field_names = list(res[0].keys())
        for r in res:
            slowest_table.add_row(r.values())
        print("\nTOP 10 SLOWEST NODES")
        print(slowest_table)

    # Most failed
    res = db.sql(f"SELECT COUNT(id) AS total_failures, class_name "
                 f"FROM {ALL_NODES_SCHEMA}.{ALL_NODES_TABLE} "
                 f"WHERE success='FAILED' "
                 f"GROUP BY class_name "
                 f"ORDER BY total_failures DESC "
                 f"LIMIT 10")

    if res:
        failed_table = PrettyTable()
        failed_table.field_names = list(res[0].keys())
        for r in res:
            failed_table.add_row(r.values())
        print("\nTOP 10 FAILED NODES")
        print(failed_table)

    # Most errored
    res = db.sql(f"SELECT COUNT(id) AS total_failures, class_name "
                 f"FROM {ALL_NODES_SCHEMA}.{ALL_NODES_TABLE} "
                 f"WHERE success='ERROR' "
                 f"GROUP BY class_name "
                 f"ORDER BY total_failures DESC "
                 f"LIMIT 10")

    if res:
        errored_table = PrettyTable()
        errored_table.field_names = list(res[0].keys())
        for r in res:
            errored_table.add_row(r.values())
        print("\nTOP 10 ERRORED NODES")
        print(errored_table)

    # Top contexts
    res = db.sql(f"SELECT COUNT(id) AS total, class_name "
                 f"FROM {ALL_NODES_SCHEMA}.{ALL_NODES_TABLE} "
                 f"WHERE IS_CONTEXT "
                 f"GROUP BY class_name "
                 f"ORDER BY total DESC "
                 f"LIMIT 10")

    if res:
        top_used_context_table = PrettyTable()
        top_used_context_table.field_names = list(res[0].keys())
        for r in res:
            top_used_context_table.add_row(r.values())
        print("\nTOP 10 MOST USED CONTEXTS")
        print(top_used_context_table)