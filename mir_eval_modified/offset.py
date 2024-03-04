'''
The goal of an offset detection algorithm is to automatically determine when
notes are played in a piece of music.  The primary method used to evaluate
onset detectors is to first determine which estimated onsets are "correct",
where correctness is defined as being within a small window of a reference
onset.

Based in part on this script:

    https://github.com/CPJKU/onset_detection/blob/master/onset_evaluation.py

Conventions
-----------

Onsets should be provided in the form of a 1-dimensional array of onset
times in seconds in increasing order.

Metrics
-------

* :func:`mir_eval.onset.f_measure`: Precision, Recall, and F-measure scores
  based on the number of esimated onsets which are sufficiently close to
  reference onsets.
'''
from . import util_mod
import collections
import numpy as np
import warnings
import pandas as pd

# The maximum allowable beat time
MAX_TIME = 30000.



def validate(reference_offsets, estimated_offsets):
    """Checks that the input annotations to a metric look like valid onset time
    arrays, and throws helpful errors if not.

    Parameters
    ----------
    reference_onsets : np.ndarray
        reference onset locations, in seconds
    estimated_onsets : np.ndarray
        estimated onset locations, in seconds

    """
    # If reference or estimated onsets are empty, warn because metric will be 0
    if reference_offsets.size == 0:
        warnings.warn("Reference onsets are empty.")
    if estimated_offsets.size == 0:
        warnings.warn("Estimated onsets are empty.")
    for onsets in [reference_offsets, estimated_offsets]:
        util_mod.validate_events(onsets, MAX_TIME)



def f_measure(reference_onsets, reference_offsets, estimated_offsets, window=.05):
    """Compute the F-measure of correct vs incorrectly predicted onsets.
    "Corectness" is determined over a small window or within a collar_time.

    Examples
    --------
    >>> reference_onsets = mir_eval.io.load_events('reference.txt')
    >>> estimated_onsets = mir_eval.io.load_events('estimated.txt')
    >>> F, P, R = mir_eval.onset.f_measure(reference_onsets,
    ...                                    estimated_onsets)

    Parameters
    ----------
    reference_offsets : np.ndarray
        Reference onset locations, in seconds
    estimated_offsets : np.ndarray
        Estimated onset locations, in seconds
    window : float
        Window size, in seconds for precise matching.
        (Default value = .05)
    collar_time : float
        Percentage of total event duration within which estimated offset
        matches reference offset.
        (Default value = 0.5)

    Returns
    -------
    f_measure : float
        2*precision*recall/(precision + recall)
    precision : float
        (# true positives)/(# true positives + # false positives)
    recall : float
        (# true positives)/(# true positives + # false negatives)
    TP : np.ndarray
        True positive offsets
    FP : np.ndarray
        False positive offsets
    FN : np.ndarray
        False negative offsets
    """


    validate(reference_offsets, estimated_offsets)
    # If either list is empty, return 0s
    if reference_offsets.size == 0 or estimated_offsets.size == 0:
        return 0., 0., 0., [], estimated_offsets, reference_offsets

    # Compute the best-case matching between reference and estimated onset
    # locations
    matching = util_mod.match_events(reference_offsets, estimated_offsets, window)

    if len(matching) == 0:
        return 0., 0., 0., [], estimated_offsets, reference_offsets
    
    matched_reference = list(list(zip(*matching))[0])
    matched_estimated = list(list(zip(*matching))[1])

    ref_indexes = np.arange(len(reference_offsets))
    est_indexes = np.arange(len(estimated_offsets))
    unmatched_reference = set(ref_indexes) - set(matched_reference)
    unmatched_estimated = set(est_indexes) - set(matched_estimated)

    TP = estimated_offsets[matched_estimated]  
    FP = estimated_offsets[list(unmatched_estimated)]
    FN = reference_offsets[list(unmatched_reference)]

    # Calculate precision and recall
    precision = float(len(matching))/len(estimated_offsets)
    recall = float(len(matching))/len(reference_offsets)

    # THIS IS THE MODIFIED PART TO CHECK THE COLLAR TIME OF HALF TIME OF TE DURATION OF THE EVENT
    # Validate offset based on maximum misalignment
    for i, ref_offset in enumerate(reference_offsets):
        for j, est_offset in enumerate(estimated_offsets):
            # Calculate permitted maximum misalignment allowed
            max_misalignment = 0.5 * (ref_offset - reference_onsets[i])
            if abs(ref_offset - est_offset) <= max_misalignment:
                TP = np.append(TP, est_offset)
                matched_estimated.append(j)
                matched_reference.append(i)
                break

    # Update unmatched references and estimated
    unmatched_reference = set(ref_indexes) - set(matched_reference)
    unmatched_estimated = set(est_indexes) - set(matched_estimated)
    FP = np.append(FP, estimated_offsets[list(unmatched_estimated)])
    FN = np.append(FN, reference_offsets[list(unmatched_reference)])

    # Recalculate precision and recall after considering collar_time
    precision = float(len(TP)) / (len(TP) + len(FP))
    recall = float(len(TP)) / (len(TP) + len(FN))

    # Compute F-measure
    f_measure = 2 * precision * recall / (precision + recall)

    return f_measure, precision, recall, TP, FP, FN

    



