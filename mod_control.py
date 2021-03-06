import talib
import numpy
import glob
import os
import gzip
import json
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates
from datetime import datetime
from csv_convert import to_csv
import sys
depth_dir = 'W:/depths/*'


def get_data(path):
    file = gzip.open(path)
    raw = file.read()
    data = json.loads(raw.decode('utf-8'))
    file.close()
    return data


def get_timestamp_from_path(file_path):
    """Get timestamp from a file path

    :param file_path: A file's path
    :type file_path: str
    :returns: integer timestamp
    """
    return int(file_path.split('_')[1].split('.')[0])


def get_file_paths(dir_path, start_date, end_date):
    """From a directory, get the full path of files for a certain period

    :param dir_path: The path of the directory wich contains the files, must end with "/*"
    :param start_date: Unix timestamp for the start of the period
    :param end_date: Unix timestamp for the end of the period
    :type dir_path: str
    :type start_date: int
    :type end_date: int
    :returns: List of path strings and list of their timestamps
    """
    # Path must end with "/*"
    if dir_path[-2:] != '/*':
        raise Exception('Path must end with "/*"')

    # Get list of files
    list_of_files = glob.glob(dir_path)

    # Get first and last files (acording to last modified time)
    first_file = min(list_of_files, key=os.path.getctime)
    latest_file = max(list_of_files, key=os.path.getctime)

    # Get timestamps of first and last files
    first_file_ts = get_timestamp_from_path(first_file)
    last_file_ts = get_timestamp_from_path(latest_file)

    # Check if we have enought files for period
    if first_file_ts > start_date:
        raise Exception('The provided start_date does not exist in files.')
    if last_file_ts < end_date:
        raise Exception('The provided end_date does not exist in files.')

    # Get list of file paths for period (and their timestamps)
    paths, stamps = [], []
    for file_path in list_of_files:
        timestamp = get_timestamp_from_path(file_path)
        # print(start_date/1000,timestamp/1000, end_date/1000)

        paths.append(file_path)
        stamps.append(timestamp)


        # if start_date >= timestamp <= end_date:
        #     paths.append(file_path)
        #     stamps.append(timestamp)
        # elif timestamp > end_date:
        #     return paths, stamps
    return paths, stamps


def get_rolling_window(start_date, end_date, interval):
    step = 1

    # Because depth was snapshotted at 10s intervals,
    # we sample by step of 10 seconds * desired interval
    if interval != 1:
        step = int(interval / 10000)

    paths, dates = get_file_paths(depth_dir, start_date, end_date)

    # Every step is an interval length
    window_paths, window_dates, curr_date_idx = [], [], 0
    while curr_date_idx < len(dates):
        curr_date = dates[curr_date_idx]
        path = paths[dates.index(curr_date)]
        window_paths.append(path)
        window_dates.append(curr_date)
        curr_date_idx += step

    return window_paths, window_dates


def get_prices(paths, side):
    """Check inside files from a list of paths and retrieve the prices for all pairs.

    :param paths: Strings of paths
    :type paths: list
    :param side: 'asks' or 'bids'
    :type side: str
    :returns: List of prices and dates tuples
    """
    prices = {}

    for path in paths:
        data = get_data(path)

        for pair in data.keys():

            if pair not in prices:
                prices[pair] = []

            if side == 'bids':  # Best bid

                bids = data[pair]['bids'].keys()
                float_bids = [float(b) for b in bids]
                sorted_bids = sorted(float_bids)
                best_bid = sorted_bids[-1]
                prices[pair].append(best_bid)

            elif side == 'asks':  # Best ask

                asks = data[pair]['asks'].keys()
                float_asks = [float(a) for a in asks]
                sorted_asks = sorted(float_asks)
                best_ask = sorted_asks[0]
                prices[pair].append(best_ask)

            else:
                raise Exception('Side must be either "asks" or "bids".')

    return prices


def show_plot(pair, dates, prices, indicator):
    xs = matplotlib.dates.date2num(dates)
    hfmt = matplotlib.dates.DateFormatter('%m/%d %H:%M')
    fig = plt.figure()
    fig.suptitle(pair, fontsize=14)
    ax = fig.add_subplot(1, 1, 1)
    ax.xaxis.set_major_formatter(hfmt)
    plt.setp(ax.get_xticklabels(), rotation=15)
    ax.plot(xs, prices)

    ax2 = fig.add_subplot(1, 1, 1)
    ax2.xaxis.set_major_formatter(hfmt)
    ax2.plot(xs, indicator)

    plt.show()


def get_moving_average(prices):
    arr = numpy.array(prices)
    output = talib.SMA(arr, timeperiod=35)
    return list(output)


def save_to_file(data):
    outfile = open('prices3.json', 'w')
    json.dump(data, outfile)
    outfile.close()


def main():
    # start_date = 1548949201435
    # end_date = 1549016566397
    # interval = 60000
    # period = 20

    start_date = 1549105984696
    end_date = 1549567124019
    interval = 1

    # Paths are required to get prices from files, dates get extracted too here
    paths, dates = get_rolling_window(start_date, end_date, interval)

    # Now we open files one by one
    prices_obj = get_prices(paths, 'bids')

    # Convert datetimes to date objects
    date_objs = [datetime.fromtimestamp(d/1000.0) for d in dates]

    prices_obj['datetime_ms'] = dates
    save_to_file(prices_obj)
    to_csv()
    for tpl in prices_obj.items():
        print(tpl[0], len(tpl[1]))

    # prices = prices_obj['XRPBTC']

    # avg = get_moving_average(prices)

    # show_plot(pair, date_objs, prices, avg)

    # Print prices and dates
    # for i, d in enumerate(date_objs):
    #     print(f'{d}  -  {prices[i]:.8f}')


if __name__ == '__main__':
    main()
