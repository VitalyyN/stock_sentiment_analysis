import requests
from urllib.parse import urlencode
from zipfile import ZipFile


base_url = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?'
links = []
with open('link.txt', 'r') as file:
    for line in file.readlines():
        links.append(line.strip())

for i in range(3):
    try:
        for index, url in enumerate(links):
            print(f'Download {index + 1} directory...\n============')
            final_url = base_url + urlencode(dict(public_key=url))
            response = requests.get(final_url)
            download_url = response.json()['href']
            download_response = requests.get(download_url)
            with open(f'modelfile{index + 1}.zip', 'wb') as f:
                f.write(download_response.content)
        else:
            break
    except Exception as ex:
        print(ex)
        continue

print('\nUnzipping files...')
with ZipFile("modelfile1.zip", "r") as myzip:
    myzip.extractall(path="stock_analysis")
with ZipFile("modelfile2.zip", "r") as myzip:
    myzip.extractall(path="stock_analysis")
