__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


import unittest

import pymongo

from all_nodes.analytics import analytics
from all_nodes.logic.logic_scene import LogicScene
from all_nodes import utils


# -------------------------------- TESTS -------------------------------- #
class StatisticsTesting(unittest.TestCase):
    def test_small_query(self):
        """
        Just make a small query to DB
        """
        utils.print_test_header("test_small_query")

        res = list(analytics.make_query({}).limit(10))

        self.assertGreater(len(res), 5)

    def test_make_wrong_query(self):
        """
        Make an impossible query DB
        """
        with self.assertRaises(pymongo.errors.OperationFailure) as e:
            analytics.make_query_aggregation(
                [
                    {
                        "$match": {
                            "success": {"$not": "FAILED"},
                            "class_name": {"$not": "666"},
                        }
                    },
                    {"$limit": 10},
                ]
            )
        print(e.exception)

    def test_submit_statistics(self):
        """
        Make a small statistics sumbission
        """
        utils.print_test_header("test_submit_statistics")

        logic_scene = LogicScene()
        n_1 = logic_scene.add_node_by_name("EmptyNode")
        n_1.run_single()

        analytics.submit_bulk_analytics([n_1.get_node_full_dict()])
