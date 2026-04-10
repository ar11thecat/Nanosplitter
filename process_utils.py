import logging
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from scipy import interpolate
from scipy import stats
from scipy.ndimage import gaussian_filter1d
from scipy.signal import fftconvolve
from scipy.signal import find_peaks

from . import decors as dc

logger = logging.getLogger(__name__)


def mean(a: ndarray, win=0, mode=None) -> ndarray:
    return _select(np.mean, win, a, mode)


def var(a: ndarray, win=0, mode=None) -> ndarray:
    return _select(np.var, win, a, mode)


def med(a: ndarray, win=0, mode=None) -> ndarray:
    return _select(np.median, win, a, mode)


def mad(a: ndarray, win=0, mode=None) -> ndarray:
    return _select(stats.median_abs_deviation, win, a, mode, scale='normal')


def zscore(a: ndarray, win=0, mode=None) -> ndarray:
    m = _select(np.mean, win, a, mode)
    s = _select(np.std, win, a, mode)
    return (a - m) / s


def medmad(a: ndarray, win=0, mode=None) -> ndarray:
    med = _select(np.median, win, a, mode)
    mad = _select(stats.median_abs_deviation, win, a, mode, scale='normal')
    return (a - med) / mad


def minmax(a: ndarray, win=0, bounds=(0, 1), mode=None) -> ndarray:
    min = _select(np.min, win, a, mode)
    max = _select(np.max, win, a, mode)
    u, v = bounds[0], bounds[1]
    return (a*(v-u) - min*v + max*u) / (max-min)


@dc.timeit(logger)
def percMinmaxNorm(a: ndarray, win=0, perc=10) -> ndarray:
    """
    custom normalisation that applies minmax between the top and bottom perc,
    then scales up so that the expected max and min sit at -1 and 1
    """
    perc_min = _spline(np.percentile, win, a, q=perc)
    perc_max = _spline(np.percentile, win, a, q=100-perc)
    scale = 50 / (50 - perc)
    return scale * ((a - perc_min) / (perc_max - perc_min) - 0.5)


def cost(id: int) -> None|function:    
    match id:
        case 0: formula = "a.shape[axis]"
        case 1: formula = "a.shape[axis] * np.log(np.var(a, axis=axis) + 1)"
        case _: return None
    def c(a: ndarray, axis: int) -> ndarray:
        return eval(formula)
    return c


@dc.timeit(logger)
def optSplit(a: ndarray, split_win: int) -> None|tuple(ndarray):
    """
    finds the split that maximises variance loss over a sliding window
    """
    if split_win % 2 == 1:
        logger.error("Split is undefined for odd windows")
        return None

    skip = 1 # minimun size of any part
    blocks_cost = _slide(cost(1), split_win, a, pad=False)
    parts_cost = [
        _slide(cost(1), i+skip, a, pad=False)
        for i in range(split_win-2*skip+1)
    ]
    joint_parts_cost = [
        parts_cost[i][:len(blocks_cost)] + parts_cost[split_win-2*skip-i][-len(blocks_cost):]
        for i in range(split_win-2*skip+1)
    ]
    joint_parts_cost = np.stack(joint_parts_cost)
    gains = blocks_cost - joint_parts_cost
    opts = np.argmax(gains, axis=0)
    idxs = opts + np.arange(len(opts)) + skip
    gains = gains[opts, np.arange(gains.shape[1])]
    return idxs, gains


@dc.timeit(logger)
def optSplitFast(a: ndarray, split_win: int, pick_win: int) -> None|tuple(ndarray):
    """
    extra fast (less accurate) version of optSplit
    """
    if split_win % 2 == 1:
        logger.error("Split is undefined for odd windows")
        return None
         
    blocks_cost = _slide(cost, split_win, a, pad=False)
    parts_cost = _slide(cost, split_win // 2, a, pad=False)
    gains = blocks_cost - (parts_cost[:-split_win // 2] + parts_cost[split_win // 2:])
    idxs = np.arange(split_win // 2, split_win // 2 + len(gains))
    opts = _slide(np.argmax, pick_win, gains, pad=False)
    opts += np.arange(len(opts))
    idxs = idxs[opts]
    gains = gains[opts]
    return idxs, gains


@dc.timeit(logger)
def optSplit_legacy(a: ndarray, split_win: int) -> None|tuple(ndarray):
    """
    slow version of optSplit, only for testing
    """
    if split_win % 2 == 1:
        logger.error("Split is undefined for odd windows")
        return None

    splits = []
    for i in range(len(a) - split_win + 1):
        w = a[i:i+split_win]
        idxs = np.arange(1, len(w))
        costs = []
        for j in idxs:
            costs.append(cost(w[:j]) + cost(w[j:]))
        opt = idxs[np.argmin(costs)]
        gain = cost(w) - np.min(costs)
        splits.append([opt + i, gain])
    splits = np.stack(splits, axis=1)
    return splits[0], splits[1]


@dc.timeit(logger)
def consensus(idxs: ndarray, vals: ndarray, win: int) -> tuple(ndarray):
    ord = np.argsort(idxs)
    idxs, vals = idxs[ord], vals[ord]
    grid = np.zeros(idxs.max() + win // 2)
    unique_idxs, bins = np.unique(idxs, return_inverse=True)
    stacked_vals = np.bincount(bins, weights=vals)
    grid[unique_idxs] = stacked_vals
    blurred_vals = gaussian_filter1d(grid, sigma=win / 2)
    peaks, _ = find_peaks(blurred_vals, prominence=0.1)
    return peaks, blurred_vals[peaks]


@dc.timeit(logger)
def consensus_obs(idxs: ndarray, vals: ndarray, win: int) -> tuple(ndarray):
    unique_idxs, bins = np.unique(idxs, return_inverse=True)
    stacked_vals = np.bincount(bins, weights=vals)
    sig = np.nonzero(stacked_vals > np.percentile(stacked_vals, q=50))[0]
    return unique_idxs[sig].astype('int'), stacked_vals[sig]


@dc.timeit(logger)
def smoothStats(a: ndarray, win: int) -> ndarray:
    k = kernel(win, "gauss")
    e = conv([a, a * a], [k])[0]
    mean = e[0]
    var = e[1] - (e[0] * e[0])
    z = (a - mean) / var
    return mean, var, z


@dc.timeit(logger)
def conv(arrs: list(ndarray), kernels: list(ndarray)) -> ndarray:
    """
    applies each kernel to each array, without leaking
    returns an ndarray with shape (arrs, kernels, len)
    """
    if all([len(a) == len(arrs[0]) for a in arrs]):
        if all([len(k) == len(kernels[0]) for k in kernels]):
            a = np.stack([[np.array(a)] for a in arrs], axis=1)
            k = np.stack([[np.array(k)] for k in kernels], axis=0)
            return fftconvolve(a, k, mode='same')
    else:
        c = [convolve(a, k) for k in kernels]
        return np.stack(c, axis=0)


def kernel(win: int, type: str) -> ndarray:
    match type:
        case "gauss":
            base = np.linspace(-2.8, 2.8, win)
            k = np.exp(-(base * base) / 2)
            return k / np.sum(k)
        case "gauss_der":
            base = np.linspace(-3, 3, win)
            k = -base * np.exp(-(base * base) / 2)
            return k / np.sum(np.absolute(k))
        case "gauss_laplace":
            base = np.linspace(-3.2, 3.2, win)
            k = (base * base - 1) * np.exp(-(base * base) / 2)
            return k / np.sum(np.absolute(k))
        case _: return np.empty()


def _select(f: function, win: int, a: ndarray, mode=None, **kwargs) -> ndarray:
    if win <= 0 or win >= len(a):
        return f(a, **kwargs)
    match mode:
        case "slide": return _slide(f, win, a, **kwargs)
        case "spline": return _spline(f, win, a, **kwargs)
        case _:
            if win < 10:
                return _slide(f, win, a, **kwargs)
            return _spline(f, win, a, **kwargs)


# @dc.timeit(logger)
def _slide(f: function, win: int, a: ndarray, pad=True, **kwargs) -> ndarray:
    """
    applies a function over a sliding window
    """
    if win <= 0 or win >= len(a):
        return f(a, **kwargs)
        
    sw_a = sliding_window_view(a, win)
    r = f(sw_a, axis=-1, **kwargs)
    if not pad:
        return r
    pad_length = win // 2
    return np.pad(r, (pad_length, win - pad_length - 1), mode = 'edge')


# @dc.timeit(logger)
def _spline(f: function, win: int, a: ndarrat, **kwargs) -> ndarray:
    """
    applies a function over overlapping windows (with 2x cover of a) and calculates the spline
    approximates the sliding window but smoother and faster for large windows
    """
    if win <= 0 or win >= len(a):
        return f(a, **kwargs)
        
    splits = len(a) // win
    excess = len(a) % win
    left_r = f(np.split(a[:-excess], splits), axis=-1, **kwargs)
    right_r = f(np.split(a[excess:], splits), axis=-1, **kwargs)
    left_x = win * np.arange(splits) + (win // 2)
    right_x = win * np.arange(splits) + (win // 2) + excess
    x = np.concatenate(([0], left_x, right_x, [len(a) - 1]))
    r = np.concatenate(([left_r[0]], left_r, right_r, [right_r[-1]]))
    ord = np.argsort(x)
    spline = interpolate.InterpolatedUnivariateSpline(
        x[ord],
        r[ord],
    )
    return spline(np.arange(len(a)))
