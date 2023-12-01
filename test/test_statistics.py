import unittest

import harperdb

from all_nodes.analytics import analytics
from all_nodes.logic.logic_scene import LogicScene
from all_nodes import utils


# -------------------------------- TESTS -------------------------------- #
class StatisticsTesting(unittest.TestCase):
    def test_small_query(self):
        """
        Just make a small query to HarperDB
        """
        utils.print_test_header("test_small_query")

        res = analytics.make_query(
            f"SELECT * "
            f"FROM {analytics.ALL_NODES_SCHEMA}.{analytics.ALL_NODES_TABLE} "
            f"LIMIT 10"
        )

        self.assertGreater(len(res), 5)

    def test_make_wrong_query(self):
        """
        Make an impossible query HarperDB
        """
        utils.print_test_header("test_make_wrong_query")

        with self.assertRaises(harperdb.exceptions.HarperDBError) as e:
            analytics.make_query(
                f"SELECT * " f"FROM {analytics.ALL_NODES_SCHEMA}.DUMMY" f"LIMIT 10"
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
