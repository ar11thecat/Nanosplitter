# Nanosplitter
## What it does
Nanosplitter finds "optimal" points to split a raw nanopore signal array into distinct squiggles, from which it extracts features to return in a feature array. It can be used purely for visualisation, or for downstream processing such as basecalling. It is meant as a Pyhton tool to use in other projects.
## Some results
For these results, I used a free dataset provided by the main Nanopore manufacturer (ONT), available at `s3://ont-open-data/chrom_acc_2025.06/raw/PAY22766/`.
### Visualisation of the squiggle splits:
1. the blue line corresponds to the normalised signal
2. the red dots correspond to split points and the confidence of the split
3. the yellow line corresponds to the average signal intensity (with std) of each squiggle

<img width="1581" height="940" alt="split_squiggles" src="https://github.com/user-attachments/assets/ba07178e-ee2e-4344-ac42-38242ebdcd11" />

### Normalisation:
Intensity distribution of the raw signal (top) and normalised signal (bottom): it is possible to see two distinct peaks correspoinding to AC-rich and CG-rich 5-mers.
The success of the normalisation is confirmed by the fact that the peaks are well defined and consistent troughout the dataset, and that they are distributed between -1 and 1.

<img width="640" height="480" alt="raw_signal_distribution" src="https://github.com/user-attachments/assets/5cc2548b-81dc-4e3c-a2e9-5529acaf11f6" />

<img width="640" height="480" alt="normalised_signal_distribution" src="https://github.com/user-attachments/assets/5a4f8008-ca37-4ca4-a4e3-929178967b69" />

## Example usage:
The following example processes and visualises the first 100 reads in the file `./sample1.pod5`:
```
from nanosplitter import normalise
from nanosplitter import split
from nanocaller import Pod5Handler


def main():

    ph = Pod5Handler("./sample1.pod5")
    ph.summary()
    reads = ph.get_signals_iter(ph.get_read_ids())
    
    for _ in range(100):
        _, signal = next(reads)
        norm_signal = normalise(signal, visualise=False)
        features = split(norm_signal, visualise=False)        

    return


if __name__ == "__main__":
    main()
```
