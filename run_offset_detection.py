import os
import glob
from tqdm import tqdm
import numpy as np
import librosa as lb
import pandas as pd
import evaluation as my_eval
from offset_detection import offset_detection_local_minimum, offset_detection_first_order, offset_detection_second_order
from mir_eval_modified.offset import f_measure
import json

EVAL_WINDOW = 0.1

# create dictionary with the duration of the calls for each chick
chick_offsets = {}

# Path to the folder containing the txt files to be evaluated
audio_folder = 'C:\\Users\\anton\\Chicks_Onset_Detection_project\Data\\normalised_data_only_inside_exp_window\\Validation_set' #CHANGE FOLDER

# metadata = pd.read_csv("C:\\Users\\anton\\Data_normalised\\Testing_set\\chicks_testing_metadata.csv")

# Path to the folder where the evaluation results will be saved
save_evaluation_results_path = r'C:\\Users\\anton\\Chicks_Onset_Detection_project\\Offset_detection\\First_order_results_validation_set' #CHANGE FOLDER new folder


if not os.path.exists(save_evaluation_results_path):
    os.makedirs(save_evaluation_results_path)


n_events_list = []
list_files = glob.glob(os.path.join(audio_folder, "*.wav"))

individual_fscores=[]
individual_precision=[]
individual_recall=[]

for file in tqdm(list_files):

    # # get ground truth (onsets, offsets)
    gt_onsets = my_eval.get_reference_onsets(file.replace('.wav', '.txt'))
    gt_offsets = my_eval.get_reference_offsets(file.replace('.wav', '.txt'))  # couple the two functions into one?

    # exp_start = metadata[metadata['Filename'] == os.path.basename(file)[:-4]]['Start_experiment_sec'].values[0]   
    # exp_end = metadata[metadata['Filename'] == os.path.basename(file)[:-4]]['End_experiment_sec'].values[0]

   
    # #get ground truth onsets, HFCpredictions_in_seconds, activation_frames inside experiment window
    # gt_onsets, gt_offsets = my_eval.discard_events_outside_experiment_window_offset_detection(exp_start, exp_end, gt_onsets, gt_offsets)

    #predicted_offsets = offset_detection_local_minimum(file, gt_onsets)

    predicted_offsets = offset_detection_first_order(file, gt_onsets, gt_offsets)

    #predicted_offsets = offset_detection_second_order(file, gt_onsets) 
    
    chick = os.path.basename(file)[:-4]

    # save gt onsets and predicted offsets into a txt file
    

    with open(os.path.join(save_evaluation_results_path, chick + 'gt_onsets_pred_offsets.txt'), 'w') as file:
        for event in zip(gt_onsets, predicted_offsets):
            file.write(str(event[0]) + ' ' + str(event[1]) + '\n')



# EVALUATION
    Fscore, precision, recall, TP, FP, FN = f_measure(gt_onsets, gt_offsets, predicted_offsets , window= EVAL_WINDOW)

    individual_fscores.append(Fscore)
    individual_precision.append(precision)
    individual_recall.append(recall)
    # save Lists of TP, FP, FN for visualisation in sonic visualiser
    evaluation_results = { 'audiofilename' : chick , 'Algorithm':'minimum_averaged_spectrogram within min-max duration calls',  'F-measure':Fscore, 'Precision':precision, 'Recall': recall}
    TP_pd = pd.DataFrame(TP, columns=['TP'])
    TP_pd.to_csv(os.path.join(save_evaluation_results_path,  f'{chick}_TP_offset.csv'), index=False)
    FP_pd = pd.DataFrame(FP, columns=['FP'])
    FP_pd.to_csv(os.path.join(save_evaluation_results_path, f'{chick}_FP_offset.csv'), index=False)
    FN_pd = pd.DataFrame(FN, columns=['FN'])
    FN_pd.to_csv(os.path.join(save_evaluation_results_path,  f'{chick}_FN_offset.csv'), index=False)

    with open(os.path.join(save_evaluation_results_path,  f"{chick}_offsets_evaluation_results.json"), 'w') as fp:
        json.dump(evaluation_results, fp)

    n_events_list.append(len(gt_offsets))

# # # compute weighted average
global_f1score_offsets = my_eval.compute_weighted_average(individual_fscores, n_events_list)
global_precision_offsets = my_eval.compute_weighted_average(individual_precision, n_events_list)
global_recall_offsets = my_eval.compute_weighted_average(individual_recall, n_events_list)

globals_results_dict= {'Offsets_global_score': {'F1-measure': global_f1score_offsets, 'Precision': global_precision_offsets, 'Recall': global_recall_offsets},}
with open(os.path.join(save_evaluation_results_path, "global_evaluation_results.json"), 'w') as fp:
    json.dump(globals_results_dict, fp)