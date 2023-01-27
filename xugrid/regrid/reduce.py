"""
Contains common reduction methods.
"""
import numpy as np


def get_method(method, methods, relative: bool):
    if isinstance(method, str):
        try:
            _method, _relative = methods[method]
            return _method, _relative
        except KeyError as e:
            raise ValueError(
                "Invalid regridding method. Available methods are: {}".format(
                    methods.keys()
                )
            ) from e
    elif callable(method):
        return method, relative
    else:
        raise TypeError("method must be a string or callable")


def mean(values, indices, weights):
    vsum = 0.0
    wsum = 0.0
    for i, w in zip(indices, weights):
        v = values[i]
        if np.isnan(v):
            continue
        vsum += w * v
        wsum += w
    if wsum == 0:
        return np.nan
    else:
        return vsum / wsum


def harmonic_mean(values, indices, weights):
    v_agg = 0.0
    w_sum = 0.0
    for i, w in zip(indices, weights):
        v = values[i]
        if np.isnan(v) or v == 0:
            continue
        if w > 0:
            w_sum += w
            v_agg += w / v
    if v_agg == 0 or w_sum == 0:
        return np.nan
    else:
        return w_sum / v_agg


def geometric_mean(values, indices, weights):
    v_agg = 0.0
    w_sum = 0.0

    # Compute sum to normalize weights to avoid tiny or huge values in exp
    normsum = 0.0
    for i, w in zip(indices, weights):
        normsum += w
    # Early return if no values
    if normsum == 0:
        return np.nan

    m = 0
    for i, w in zip(indices, weights):
        v = values[i]
        if np.isnan(v) or v == 0:
            continue
        if w > 0:
            v_agg += w * np.log(abs(v))
            w_sum += w
            if v < 0:
                m += 1

    if w_sum == 0:
        return np.nan
    else:
        return (-1.0) ** m * np.exp((1.0 / w_sum) * v_agg)


def sum(values, indices, weights):
    v_sum = 0.0
    w_sum = 0.0

    for i, w in zip(indices, weights):
        v = values[i]
        if np.isnan(v):
            continue
        v_sum += v
        w_sum += w
    if w_sum == 0:
        return np.nan
    else:
        return v_sum


def minimum(values, indices, weights):
    vmin = values[indices[0]]
    for i in indices:
        v = values[i]
        if np.isnan(v):
            continue
        if v < vmin:
            vmin = v
    return vmin


def maximum(values, indices, weights):
    vmax = values[indices[0]]
    for i in indices:
        v = values[i]
        if np.isnan(v):
            continue
        if v > vmax:
            vmax = v
    return vmax


def mode(values, indices, weights):
    # Area weighted mode
    # Reuse weights to do counting: no allocations
    # The alternative is defining a separate frequency array in which to add
    # the weights. This implementation is less efficient in terms of looping.
    # With many unique values, it keeps having to loop through a big part of
    # the weights array... but it would do so with a separate frequency array
    # as well. There are somewhat more elements to traverse in this case.
    s = indices.size
    w_sum = 0
    for running_total, (i, w) in enumerate(zip(indices, weights)):
        v = values[i]
        if np.isnan(v):
            continue
        w_sum += 1
        for j in range(running_total):  # Compare with previously found values
            if values[j] == v:  # matches previous value
                weights[j] += w  # increase previous weight
                break

    if w_sum == 0:  # It skipped everything: only nodata values
        return np.nan
    else:  # Find value with highest frequency
        w_max = 0
        for i in range(s):
            w = weights[i]
            if w > w_max:
                w_max = w
                v = values[i]
        return v


def median(values, indices, weights):
    # TODO: more efficient implementation?
    # See: https://github.com/numba/numba/blob/0441bb17c7820efc2eba4fd141b68dac2afa4740/numba/np/arraymath.py#L1693
    return np.nanpercentile(values[indices], 50)


def conductance(values, indices, weights):
    # Uses relative weights!
    # Rename to: first order conservative?
    v_agg = 0.0
    w_sum = 0.0
    for i, w in zip(indices, weights):
        v = values[i]
        if np.isnan(v):
            continue
        v_agg += v * w
        w_sum += w
    if w_sum == 0:
        return np.nan
    else:
        return v_agg


def max_overlap(values, indices, weights):
    max_w = 0.0
    v = np.nan
    for i, w in zip(indices, weights):
        if w > max_w:
            max_w = w
            v_temp = values[i]
            if np.isnan(v_temp):
                continue
            v = v_temp
    return v


OVERLAP_METHODS = {
    "mean": (mean, False),
    "harmonic_mean": (harmonic_mean, False),
    "geometric_mean": (geometric_mean, False),
    "sum": (sum, False),
    "minimum": (minimum, False),
    "maximum": (maximum, False),
    "mode": (mode, False),
    "median": (median, False),
    "conductance": (conductance, True),
    "max_overlap": (max_overlap, False),
}
