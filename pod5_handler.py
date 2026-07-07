import logging
import numpy as np
from pathlib import Path
import pod5


logger = logging.getLogger(__name__)


class Pod5Handler:

    def __init__(self, pod5_path: str):

        self.pod5_path = Path(pod5_path)


    @property
    def pod5_path(self) -> Path:
        return self._pod5_path


    @pod5_path.setter
    def pod5_path(self, pod5_path: Path):

        if pod5_path.exists() and pod5_path.name.endswith(".pod5"):
            logger.info(f"Set pod5 file to {pod5_path.resolve()}")
            self._pod5_path = pod5_path

        else:
            logger.error(f"Unrecognised pod5 path: {pod5_path.resolve()}")


    def summary(self):
        """
            prints a summary of the .pod5 file
        """

        logger.info(f"Printing summary of {self._pod5_path.name}...")

        with pod5.Reader(self._pod5_path) as reader:
            print(f"\n[ Summary of '{self._pod5_path.name}'':")
            print(f"[ Number of batches: {reader.batch_count}")
            print(f"[ Number of reads: {reader.num_reads}")
            print()


    def get_read_ids(self) -> set[str]:
        """
            returns a list with all the read ids in the .pod5 file
        """

        logger.info(f"Gathering read ids from {self._pod5_path.name}...")

        with pod5.Reader(self._pod5_path) as reader:
             return set(reader.read_ids)


    def get_signals_iter(self, read_ids: set[str], batch=0) -> iter[tuple[str, np.array]]:
        """
            returns an iterator with the signals for all the input read ids
        """

        logger.info(f"Initiating iterator for signals from {self._pod5_path.name}...")

        if batch == 0:
            chunks = [list(read_ids)]
        else:
            read_ids = sorted(list(read_ids))
            chunks = [set(read_ids[i:i + batch]) for i in range(0, len(read_ids), batch)]
            
        with pod5.Reader(self._pod5_path) as reader:

            for chunk in chunks:
                for record in reader.reads(selection=chunk):
                    yield (str(record.read_id), record.signal)
                
