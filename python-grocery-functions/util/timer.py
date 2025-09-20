import logging
import time


class Timer:
    def __init__(self):
        self.start_times = {}

    def start(self, label):
        self.start_times[label] = time.time()

    def timeLog(self, label, comment=""):
        if label not in self.start_times:
            raise Exception(f"Timer with label '{label}' not started.")

        elapsed_time = time.time() - self.start_times[label]
        logging.info(f"{label} {comment}: {elapsed_time:.2f} seconds")

    def stop(self, label):
        if label not in self.start_times:
            raise Exception(f"Timer with label '{label}' not started.")

        elapsed_time = time.time() - self.start_times[label]
        logging.info(f"{label} ended. Total time: {elapsed_time:.2f} seconds")
        del self.start_times[label]
