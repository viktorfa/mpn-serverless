import traceback
import logging
from pymongo.errors import OperationFailure


def log_traceback(ex, ex_traceback=None):
    if ex_traceback is None:
        ex_traceback = ex.__traceback__
    tb_lines = [
        line.rstrip("\n")
        for line in traceback.format_exception(ex.__class__, ex, ex_traceback)
    ]
    if isinstance(ex, OperationFailure):
        logging.error(ex.details)
    logging.error(tb_lines)
