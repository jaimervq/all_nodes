# -*- coding: UTF-8 -*-
__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


import polars as pl

from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


class PolarsCsv(GeneralLogicNode):
    INPUTS_DICT = {
        "in_csv_filepath": {"type": str},
    }

    OUTPUTS_DICT = {"out_dataframe": {"type": pl.DataFrame}}

    def run(self):
        import os

        in_csv_filepath = self.get_attribute_value("in_csv_filepath")

        if not os.path.isfile(in_csv_filepath):
            self.fail("CSV file {} does not exist!".format(in_csv_filepath))
            return

        self.set_output("out_dataframe", pl.read_csv(in_csv_filepath))


class PolarsParquet(GeneralLogicNode):
    INPUTS_DICT = {
        "in_parquet_filepath": {"type": str},
    }

    OUTPUTS_DICT = {"out_dataframe": {"type": pl.DataFrame}}

    def run(self):
        import os

        in_parquet_filepath = self.get_attribute_value("in_parquet_filepath")

        if not os.path.isfile(in_parquet_filepath):
            self.fail("Parquet file {} does not exist!".format(in_parquet_filepath))
            return

        self.set_output("out_dataframe", pl.read_parquet(in_parquet_filepath))
