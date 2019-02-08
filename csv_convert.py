import json
from collections import OrderedDict
from datetime import datetime


def to_csv():
    with open('prices3.json') as json_f, open('prices2.csv', 'w') as csv_f:
        json_data = OrderedDict(json.loads(json_f.read()))

        # Create / write the header
        header = 'datetime'
        for pair in json_data.keys():
            if pair != 'datetime_ms':
                header += ',' + pair
        csv_f.write(header + '\n')

        # Write data
        data = ''
        for idx in range(0, len(json_data['BTCUSDT'])):
            line = f"{json_data['datetime_ms'][idx]}"  # Date is originally last but we want it first

            for pair in json_data.keys():
                if pair != 'datetime_ms':
                    line += f',{json_data[pair][idx]}'
                # if pair == 'BTCUSDT':
                #     print(json_data[pair][idx], datetime.fromtimestamp(json_data['datetime_ms'][idx]/1000.0))

            data += line + '\n'

        csv_f.write(data)
