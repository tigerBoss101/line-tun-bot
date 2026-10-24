import base64
import csv
import io
import requests


def main():
    response = requests.get("https://www.vpngate.net/api/iphone/")
    with io.StringIO(response.text) as file:
        csv_reader = csv.reader(file, delimiter=",")
        for row in csv_reader:
            if "TH" not in row:
                continue
            config_file = base64.b64decode(row[-1]).decode()
            if "\nproto udp" in config_file:
                continue
            print(config_file)
            return


if __name__ == "__main__":
    main()
