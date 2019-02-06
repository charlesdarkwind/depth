import glob
import os
import gzip
import json
import matplotlib.pyplot as plt
from datetime import datetime

depth_dir = 'W:/depths-old/*'
ROLLING_WINDOW = 50


def ts_to_date(ts):
    return datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')


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

        if start_date >= timestamp <= end_date:
            paths.append(file_path)
            stamps.append(timestamp)
        elif timestamp > end_date:
            return paths, stamps


def get_rolling_window(start_date, end_date, interval, period):
    # Because depth was snapshotted at 10s intervals
    step = int(interval / 10000)

    # Need more data than window to compute first val
    real_start_date = start_date - (interval*period)

    paths, dates = get_file_paths(depth_dir, real_start_date, end_date)

    # Every step is an interval length
    window_paths, window_dates, curr_date_idx = [], [], 0
    while curr_date_idx < len(dates):
        curr_date = dates[curr_date_idx]
        path = paths[dates.index(curr_date)]
        window_paths.append(path)
        window_dates.append(curr_date)
        curr_date_idx += step

    return window_paths, window_dates


def get_prices(paths, pair, side):
    """Get prices list from files path

    :param paths: Strings of paths
    :type paths: list
    :param pair: Pair string
    :type pair: str
    :param side: 'asks' or 'bids'
    :type side: str
    :returns: List of prices and dates tuples
    """
    prices = []
    for path in paths:
        data = get_data(path)

        if side == 'bids':
            bid = list(data[pair]['bids'].keys())[-1]
            prices.append(bid)
        elif side == 'asks':
            ask = list(data[pair]['asks'].keys())[0]
            prices.append(ask)
        else:
            raise Exception(' must be either "asks" or "bids".')

    return prices


def main():
    (start_date, end_date, interval, period) = (1548949201435, 1549016566397, 60000, 20)
    paths, dates = get_rolling_window(start_date, end_date, interval, period)
    prices_str = get_prices(paths, 'XRPBTC', 'bids')

    prices = [float(i) for i in prices_str]
    dates_human = [ts_to_date(d/1000) for d in dates]

    plt.plot(dates_human, prices)
    plt.show()

    # Print prices and dates
    for i, d in enumerate(dates_human):
        print(f'{d}  {prices[i]:.8f}')


if __name__ == '__main__':
    main()
