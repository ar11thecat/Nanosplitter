import h5py
import logging
import matplotlib.pyplot as plt
import os
import numpy as np
from pathlib import Path
import sys
import time

from . import decors as dc
from . import utils as u
from . import process_utils as pu
from .pbar import PBar


logger = logging.getLogger(__name__)


class CallTrainer:

    def __init__(self, sigseq_path: str=""):

        self.ss_path: Path = sigseq_path
        self.curr_read_id: str = 'paperino'


    @property
    def ss_path(self) -> Path:
        return self._ss_path


    @ss_path.setter
    def ss_path(self, path: str):

        if Path.exists(path):
            if path.endswith(".h5"):
                self._ss_path = Path(f"./{path}")
            else:
                try_dir = Path(f"./{path}")
        else:
            try_dir = Path("./")
        
        if find := u.find_exts_rec(dir=try_dir, exts=[".h5"]):
            self._ss_path = find[0]
        else:
            logger.error(f"No '.h5' files found in {try_dir.resolve()}")
            return

        logger.info(f"Set sigseq file to {self._ss_path.resolve()}")

    word = 'pippo'
    @dc.embellish(logger,
                  message="Iterating sigseq data...")
    def iter_reads(self) -> iter:
            
        with h5py.File(self._ss_path, "r") as f:

            for id_ in f:
                self.curr_read_id = id_
                signal = f[id_]["signal"][:]
                sequence = f[id_].attrs["sequence"]

                print(f"{'='*os.get_terminal_size().columns}")
                logger.info(f"ANALYSING READ {self.curr_read_id}")
                print(f"{'='*os.get_terminal_size().columns}")
                
                yield id_, signal, sequence
                

    @staticmethod
    @dc.embellish(logger,
                  message="Applying percentile minmax normalisation...",
                  appx=f"{'-'*os.get_terminal_size().columns}")
    @dc.timeit(logger, separate=True)
    def normalise(sig: ndarray, visualise=False) -> ndarray:

        norm_sig = pu.percMinmaxNorm(sig, 10000)

        if visualise:
            plt.hist(norm_sig, bins=50)
            plt.show()
        
        return norm_sig


    @staticmethod
    @dc.embellish(logger,
                  message="Splitting squiggle with optimal splits...",
                  appx=f"{'-'*os.get_terminal_size().columns}")
    @dc.timeit(logger, separate=True)
    def split(sig: ndarray, visualise=False) -> ndarray:
        
        opts_1, gains_1 = pu.optSplit(sig, 24)
        opts_2, gains_2 = pu.optSplit(sig, 12)
        opts = np.concatenate([opts_1, opts_2], axis=0)
        gains = np.concatenate([gains_1, gains_2], axis=0)
        splits, vals = pu.consensus(opts, gains, 4)
        squigs = np.split(sig, splits)
        features = CallTrainer.featLoader(squigs)

        if visualise:
            plt.plot(sig)
            plt.scatter(splits + 0.5, pu.minmax(vals), color='red')
            visual = np.concatenate([
                [
                    np.full(f[-1].astype('int'), f[0]),
                    np.full(f[-1].astype('int'), f[0] + f[1]),
                    np.full(f[-1].astype('int'), f[0] - f[1]),
                ] for f in features
            ], axis=1)
            plt.plot(visual[0], color='orange')
            plt.plot(visual[1], color='orange', linestyle='--')
            plt.plot(visual[2], color='orange', linestyle='--')
            plt.show()

        return features


    def train(self):
        pass
    

    @staticmethod
    @dc.timeit(logger)
    def featLoader(squigs: list(ndarray)) -> ndarray:
        lengths = np.array([len(s) for s in squigs])
        max_len = np.percentile(lengths, q=95).astype('int')
        padded = np.full((len(squigs), max_len), np.nan)
        for i, s in enumerate(squigs):
            if len(s) > max_len:
                s = s[:max_len]
            padded[i, :len(s)] = s
        features = np.stack([
            medians := np.nanmedian(padded, axis=1),
            mads := np.nanmedian(np.abs(padded - medians[:, None]), axis=1),
            lengths,
        ], axis=1)

        return features
