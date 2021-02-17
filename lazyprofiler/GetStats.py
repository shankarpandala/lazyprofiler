#!/usr/bin/env python

# log_gpu_cpu_stats
#   Logs GPU and CPU stats either to stdout, or to a CSV file.
#   See usage below.

# Copyright (c) 2019,  Scott C. Lowe <scott.code.lowe@gmail.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in
#       the documentation and/or other materials provided with the distribution
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from __future__ import print_function

import datetime
import psutil
import subprocess
import sys
import time
import contextlib
import os
import pandas as pd
import math
import multiprocessing as mp


@contextlib.contextmanager
def smart_open(filename=None, mode="a"):
    """
    Context manager which can handle writing to stdout as well as files.

    If filename is None, the handle yielded is to stdout. If writing to
    stdout, the connection is not closed when leaving the context.
    """
    if filename:
        hf = open(filename, mode)
    else:
        hf = sys.stdout

    try:
        yield hf
    finally:
        if hf is not sys.stdout:
            hf.close()


def check_nvidia_smi():
    try:
        subprocess.check_output(["nvidia-smi"])
    except FileNotFoundError:
        raise EnvironmentError("The nvidia-smi command could not be found.")


try:
    check_nvidia_smi()
except:
    pass


class Logger:
    def __init__(
        self,
        fname=None,
        style=None,
        date_format=None,
        refresh_interval=1,
        iter_limit=None,
        show_header=True,
        header_only_once=True,
        show_units=True,
        sep=",",
    ):

        self.fname = fname if fname else None
        if style is not None:
            self.style = style
        elif self.fname is None:
            self.style = "tabular"
        else:
            self.style = "csv"
        self.date_format = date_format
        self.refresh_interval = refresh_interval
        self.iter_limit = iter_limit
        self.show_header = show_header
        self.header_only_once = header_only_once
        self.header_count = 0
        self.show_units = show_units
        self.sep = sep
        self.col_width = 10
        self.time_field_width = (
            15
            if self.date_format is None
            else max(self.col_width, len(time.strftime(self.date_format)))
        )

        if self.date_format is None:
            self.time_field_name = "Timestamp" + (" (s)" if self.show_units else "")
        else:
            self.time_field_name = "Time"

        self.cpu_field_names = [
            "CPU" + (" (%)" if self.show_units else ""),
            "RAM" + (" (%)" if self.show_units else ""),
            "Swap" + (" (%)" if self.show_units else ""),
        ]
        self.gpu_field_names = [
            "GPU" + (" (%)" if self.show_units else ""),
            "Mem" + (" (%)" if self.show_units else ""),
            "Temp" + (" (C)" if self.show_units else ""),
        ]
        self.gpu_queries = [
            "utilization.gpu",
            "utilization.memory",
            "temperature.gpu",
        ]
        self.gpu_query = ",".join(self.gpu_queries)

        self.gpu_names = self.get_gpu_names()

    def get_gpu_names(self):
        try:
            res = subprocess.check_output(["nvidia-smi", "-L"])
            return [i_res for i_res in res.decode().split("\n") if i_res != ""]
        except:
            pass

    @property
    def tabular_format(self):
        fmt = "{:>" + str(self.time_field_width) + "} |"
        fmt += ("|{:>" + str(self.col_width) + "} ") * len(self.cpu_field_names)
        try:
            for i_gpu in range(len(self.gpu_names)):
                fmt += "|"
                fmt += ("|{:>" + str(self.col_width) + "} ") * len(self.gpu_field_names)
        except:
            pass
        return fmt

    def write_header_csv(self):
        """
        Write header in CSV format.
        """
        with smart_open(self.fname, "a") as hf:
            print(self.time_field_name + self.sep, end="", file=hf)
            print(*self.cpu_field_names, sep=self.sep, end="", file=hf)
            try:
                for i_gpu in range(len(self.gpu_names)):
                    print(self.sep, end="", file=hf)
                    print(
                        *["{}:{}".format(i_gpu, fn) for fn in self.gpu_field_names],
                        sep=self.sep,
                        end="",
                        file=hf
                    )
            except:
                pass
            print("\n", end="", file=hf)  # add a newline

    def write_header_tabular(self):
        """
        Write header in tabular format.
        """
        with smart_open(self.fname, "a") as hf:
            cols = [self.time_field_name]
            cols += self.cpu_field_names
            try:
                for i_gpu in range(len(self.gpu_names)):
                    cols += ["{}:{}".format(i_gpu, fn) for fn in self.gpu_field_names]
            except:
                pass

            print(self.tabular_format.format(*cols), file=hf)

            # Add separating line
            print("-" * (self.time_field_width + 1), end="", file=hf)
            print(
                "+",
                ("+" + "-" * (self.col_width + 1)) * len(self.cpu_field_names),
                sep="",
                end="",
                file=hf,
            )
            try:
                for i_gpu in range(len(self.gpu_names)):
                    print(
                        "+",
                        ("+" + "-" * (self.col_width + 1)) * len(self.gpu_field_names),
                        sep="",
                        end="",
                        file=hf,
                    )
            except:
                pass
            print("\n", end="", file=hf)  # add a newline

    def write_header(self):
        if self.style == "csv":
            self.write_header_csv()
        elif self.style == "tabular":
            self.write_header_tabular()
        else:
            raise ValueError("Unrecognised style: {}".format(self.style))
        self.header_count += 1

    def poll_cpu(self):
        """
        Fetch current CPU, RAM and Swap utilisation

        Returns
        -------
        float
            CPU utilisation (percentage)
        float
            RAM utilisation (percentage)
        float
            Swap utilisation (percentage)
        """
        return (
            psutil.cpu_percent(),
            psutil.virtual_memory().percent,
            psutil.swap_memory().percent,
        )

    def poll_gpus(self, flatten=False):
        """
        Query GPU utilisation, and sanitise results

        Returns
        -------
        list of lists of utilisation stats
            For each GPU (outer list), there is a list of utilisations
            corresponding to each query (inner list), as a string.
        """
        res = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=" + self.gpu_query,
                "--format=csv,nounits,noheader",
            ]
        )
        lines = [i_res for i_res in res.decode().split("\n") if i_res != ""]
        data = [
            [
                val.strip() if "Not Supported" not in val else "N/A"
                for val in line.split(",")
            ]
            for line in lines
        ]
        if flatten:
            data = [y for row in data for y in row]
        return data

    def write_record(self):
        with smart_open(self.fname, "a") as hf:
            stats = list(self.poll_cpu())
            if self.date_format is None:
                t = "{:.3f}".format(time.time())
            else:
                t = time.strftime(self.date_format)
            stats.insert(0, t)
            try:
                stats += self.poll_gpus(flatten=True)
            except:
                pass
            if self.style == "csv":
                print(",".join([str(stat) for stat in stats]), file=hf)
            elif self.style == "tabular":
                print(self.tabular_format.format(*stats), file=hf)
            else:
                raise ValueError("Unrecognised style: {}".format(self.style))

    def __call__(self, n_iter=None):
        if self.show_header and (self.header_count < 1 or not self.header_only_once):
            self.write_header()
        n_iter = self.iter_limit if n_iter is None else n_iter
        i_iter = 0
        while True:
            t_begin = time.time()
            self.write_record()
            i_iter += 1
            if n_iter is not None and n_iter > 0 and i_iter >= n_iter:
                break
            t_sleep = self.refresh_interval + t_begin - time.time() - 0.001
            if t_sleep > 0:
                time.sleep(t_sleep)

def start_log(file_name=None):
    if file_name is not None:
        if os.path.isfile(file_name + ".csv"):
            os.remove(file_name + ".csv")
        logger_fname = file_name + ".csv"
    else:
        if os.path.isfile("log_compute.csv"):
            os.remove("log_compute.csv")
        logger_fname = "log_compute.csv"

    proc = mp.Process(target=Logger(fname=logger_fname, refresh_interval=0.2))
    proc.start()

    print("Started logging compute utilisation")
    return proc


def stop_log(pid=None):
    pid.terminate()
    print("Terminated the compute utilisation logger background process")


def plot_stats(file_name=None, save_plot=False):
    if file_name is not None:
        logger_fname = file_name + ".csv"
    else:
        logger_fname = "log_compute.csv"
    log_data = pd.read_csv(logger_fname)
    log_data["Timestamp (s)"] = pd.to_datetime(log_data["Timestamp (s)"], unit="s")
    log_data.set_index("Timestamp (s)", inplace=True)
    plot_rows = int(math.ceil(len(log_data.columns) / 3))

    if save_plot is True:
        return log_data.plot(
            subplots=True, layout=(plot_rows, 3), figsize=(16, 4 * plot_rows)
        )
    else:
        log_data.plot(subplots=True, layout=(plot_rows, 3), figsize=(16, 4 * plot_rows))
