__author__ = "Jaime Rivera <jaime.rvq@gmail.com>"
__copyright__ = "Copyright 2022, Jaime Rivera"
__credits__ = []
__license__ = "MIT License"


from all_nodes.logic.logic_node import GeneralLogicNode
from all_nodes import utils


LOGGER = utils.get_logger(__name__)


class EnvironToYmlCtx(GeneralLogicNode):
    IS_CONTEXT = True
    OUTPUTS_DICT = {"yaml_filepath": {"type": str}}
