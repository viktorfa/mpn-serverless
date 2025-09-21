import logging
import traceback


def log_traceback(ex, ex_traceback=None):
    if ex_traceback is None:
        ex_traceback = ex.__traceback__
    tb_lines = [line.rstrip("\n") for line in traceback.format_exception(ex.__class__, ex, ex_traceback)]
    logging.error(tb_lines)
