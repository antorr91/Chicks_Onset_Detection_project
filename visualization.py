
import os
import matplotlib.pyplot as plt
import numpy as np


def visualize_activation_and_gt(plot_dir,file_name, onset_detection_funtion_name, gt_onsets, activation, hop_length=441, sr=44100):  
    """Visualize the onsets and save the plot.

    Args:
        onset_detection_funtion_name (str): Name of the onset detection function.
        gt_onsets (list): List of ground truth onsets.
        activation (list): List of activation values.
        file_name (str): Name of the file.
        plot_dir (str): Path to the plot directory.
        hop_length (int): Hop length in samples.
        sr (int): Sampling rate in Hz.
    """

    seconds = (np.arange(0, len(activation))) * hop_length / sr
    plt.figure(figsize=(100, 5))

    plt.plot(seconds, activation, alpha=0.8, label=onset_detection_funtion_name) 
    print(f"seconds: {seconds[:10]}")
    print(f"onset_function: {activation[:10]}")
    #reference onsets
    for i in gt_onsets :
      plt.axvline(x=i, alpha=0.3, color="g")
    # for i in predicted_onsets:
    #   plt.axvline(x=i, alpha=0.5, color="r")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    plt.title("Onsets Visualization")

    # Construct the output file path with the specified file name
    plot_filename = os.path.join(plot_dir, f"{file_name.split('.wav')[0]}_onset_plot_{onset_detection_funtion_name}_.png")
    print(f"plot_filename: {plot_filename}")
    plt.savefig(plot_filename)
    plt.close()

    print(f"Plot saved as {plot_filename}")
    return



def plot_precision_recall_thresholds(list_thresholds, list_precisions, list_recalls):
    """Plot the precision-recall curve.

    Args:
        list_thresholds (list): List of peak picking thresholds.
        list_precisions (list): List of precisions.
        list_recalls (list): List of recalls.
    """
    plt.figure(figsize=(10, 5))
    plt.plot(list_thresholds, list_precisions, label="Precision")
    plt.plot(list_thresholds, list_recalls, label="Recall")
    plt.xlabel("Threshold")
    plt.ylabel("Precision/Recall")
    plt.title("Precision-Recall Curve")
    plt.legend()
    plt.show()
    return


def plot_precision_recall_curve(list_precisions, list_recalls):
    """Plot the precision-recall curve.

    Args:
        list_precisions (list): List of precisions.
        list_recalls (list): List of recalls.
    """
    plt.figure(figsize=(10, 5))
    plt.plot(list_recalls, list_precisions)
    plt.xlabel("Recall")
    plt.ylabel("Precision")
    plt.title("Precision-Recall Curve")
    plt.show()
    return