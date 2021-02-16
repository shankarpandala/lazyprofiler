import subprocess
import os
import pandas as pd
import math

def start_log(file_name = None):
    if file_name is not None:
        if os.path.isfile(file_name+'.csv'):
            os.remove(file_name+'.csv')
        logger_fname = file_name+'.csv'
    else:
        if os.path.isfile('log_compute.csv'):
            os.remove('log_compute.csv')
        logger_fname = 'log_compute.csv'
    logger_pid = subprocess.Popen(
        ['python', 'log_gpu_cpu_stats.py',
        logger_fname,
        '--loop',  '0.2',  # Interval between measurements, in seconds (optional, default=1)
        ])
    
    print('Started logging compute utilisation')
    return logger_pid

def stop_log(pid=None):
    pid.terminate()
    print('Terminated the compute utilisation logger background process')

def plot_stats(file_name = None, save_plot=False):
    if file_name is not None:
        logger_fname = file_name+'.csv'
    else:
        logger_fname = 'log_compute.csv'
    log_data = pd.read_csv(logger_fname)
    log_data['Timestamp (s)'] = pd.to_datetime(log_data['Timestamp (s)'],unit='s')
    log_data.set_index('Timestamp (s)',inplace =True)
    plot_rows = int(math.ceil(len(log_data.columns)/3))
    
    if save_plot is True:
        return log_data.plot(subplots=True,layout=(plot_rows,3),figsize=(16,4*plot_rows))
    else:
        log_data.plot(subplots=True,layout=(plot_rows,3),figsize=(16,4*plot_rows));