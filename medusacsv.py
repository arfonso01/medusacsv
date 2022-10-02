import requests
import re
from pathlib import Path
import json
from functools import lru_cache, reduce
from transmission_rpc import Client

medusa_host = 'localhost:8081'
medusa_api_key = 'your_api_key'

transmission_rpc = Client(host='localhost', port=9091, username='myuser', password ='mypass')
my_torrents_csv = 'torrents.csv'
episode_format = 'Cap.\d+' # 's\d+e\d+' # '\d+x\d+'
separator = '-' # after title, or '\(19\d+\)|\(20\d+\)' # year after title or 'other'

global_quality_format = '\w+\s\d+\w[i-p]|\w+\d+\w[i-p]|\d+\w[i-p]\s\w+|\d+\w[i-p]\w+|'
UHD_quality_format = '4k\w+|4k\s\w+|\w+4k|\w+\s4k'

quality_format = global_quality_format + UHD_quality_format

headers_for_medusa = {
    'Content-Type': 'application/json',
    'Accept': 'application/json; charset=UTF-8',
    'x-api-key': medusa_api_key}

medusa_qualities = {1: 'Unknown', 2: 'SDTV', 4: 'SD DVD', 8: '720p HDTV', 16:'RawHD',
                    32: '1080p HDTV', 64: '720p WEB-DL', 128: '1080p WEB-DL',
                    256: '720p BluRay', 512: '1080p BluRay', 1024: '4K UHD TV',
                    2048: '4K UHD WEB-DL', 4096: '4K UHD BluRay', 8192: '8K UHD TV',
                    16384: '8K UHD WEB-DL', 32768: '8K UHD BluRay'}
candidates = []
download_list = []

path_torrents_csv = Path(my_torrents_csv)
path_torrents_csv.touch(exist_ok=True)
open_torrents_csv = map(lambda x: str.strip(x), open(my_torrents_csv).readlines())

torrents_csv = list(map(lambda x: x.split(','), open_torrents_csv))

def medusa_requests(route_parameter: str):
    request = requests.get(medusa_host + route_parameter, headers = headers_for_medusa).text
    return json.loads(request)

@lru_cache
def medusa_all_titles():
    route_parameter = '/api/v2/series?paused=1&detailed=1&page=1&limit=1000'
    return medusa_requests(route_parameter)

list_medusa = list(map(lambda x: [x.get('title'), x.get('id')['slug']], medusa_all_titles()))

def add_aliases(line: int, index: int): # line of list; index is numerical order of aliases
    if len(medusa_all_titles())-1 < line:
        return
    try:
        list_medusa.append([medusa_all_titles()[line].get('config')['aliases'][index]['title'],
                            medusa_all_titles()[line].get('id')['slug']])
        add_aliases(line, index+1)
    except IndexError:
        pass
    add_aliases(line+1, index)


add_aliases(0,0) # to list_medusa

def list_medusa_field(nfield: int): #0: 'title', 1: 'id' 
    return list(map(lambda x: x[nfield].upper() , list_medusa))

series_dict = dict(zip(list_medusa_field(0), list_medusa_field(1)))

def get_line_csv(line: int):
    return list(map(lambda x: x[1:-1].split(','), torrents_csv[line]))

def get_raw_episode(line):
    find_episode = re.findall(episode_format, str(get_line_csv(line)[0]), flags=re.IGNORECASE)
    episode_raw = re.findall('\d', str(find_episode))
    return "".join(episode_raw)

def get_episode(line):
    if len(get_raw_episode(line)) == 3:
        return 's0' + get_raw_episode(line)[0:1] + 'e' + get_raw_episode(line)[1:]
    elif len(get_raw_episode(line)) == 4:
        return 's' + get_raw_episode(line)[0:2] + 'e' + get_raw_episode(line)[2:]
    elif len(get_raw_episode(line)) == 2:
        return 's0' + get_raw_episode(line)[0:1] + 'e0' + get_raw_episode(line)[1:]
    else:
        return

def get_quality_csv(line):
    return "".join(re.findall(quality_format, str(get_line_csv(line)[0]), flags=re.IGNORECASE)).upper()

def get_title(line):
    find_separator = "".join(re.findall(separator, str(get_line_csv(line)[0]), flags=re.IGNORECASE))
    index = get_line_csv(line)[0][0].find(find_separator)
    return str.strip(get_line_csv(line)[0][0][0:index]).upper()

def quality_int(line: int, get_quality):
    if get_quality(line).find('HDTV') > -1 and get_quality(line).find('720') == -1 :
        return 2
    elif get_quality(line).find('720') > -1 and get_quality(line).find('HDTV') > -1:
        return 8
    elif get_quality(line).find('1080') > -1 and get_quality(line).find('HDTV') > -1:
        return 32
    elif get_quality(line).find('720') > -1 and get_quality(line).find('WEB') > -1:
        return 64
    elif get_quality(line).find('1080') > -1 and get_quality(line).find('WEB') > -1:
        return 128
    elif get_quality(line).find('720') > -1 and get_quality(line).find('BLU') > -1:
        return 256
    elif get_quality(line).find('1080') > -1 and get_quality(line).find('BLU') > -1:
        return 512
    elif re.findall('4K', get_quality(line)) == '4K' and re.findall('TV', get_quality(line)) == 'TV':
        return 1024
    elif re.findall('4K', get_quality(line))[0] == '4K' and re.findall('WEB', get_quality(line))[0] == 'WEB':
        return 2048
    elif re.findall('4K', get_quality(line)) == '4K' and re.findall('BLU', get_quality(line)) == 'BLU':
        return 4096
    else:
        return 1

def episode_status_quality(line):
    page = '/api/v2/series/' + series_dict[get_title(line)].lower()
    subpage = '/episodes/' + get_episode(line)
    route_parameter = page + subpage
    return medusa_requests(route_parameter)

def serie_qualities(line):
    route_parameter = '/api/v2/series/' + series_dict[get_title(line)].lower()
    return medusa_requests(route_parameter)

def filter_for_status(line):
    if get_title(line) not in list_medusa_field(0):
        pass
    else:
        status = episode_status_quality(line).get('status')
        if status == 'Skipped' or status == 'Ignored' or status == 'Archived':
            pass
        else:
            return [get_title(line) + ' ' + get_episode(line),
                    medusa_qualities[quality_int(line, get_quality_csv)],
                    quality_int(line, get_quality_csv),
                    series_dict[get_title(line)].lower(),
                    episode_status_quality(line).get('status'),
                    episode_status_quality(line).get('quality'),
                    get_line_csv(line)[2][0]]

def adding_to_download_candidate_lists(line):
    if len(torrents_csv) <= line:
        return
    if filter_for_status(line) == None:
        pass
    else:
        quality = quality_int(line, get_quality_csv)
        alowed = serie_qualities(line).get('config')['qualities']['allowed']
        preferred = serie_qualities(line).get('config')['qualities']['preferred']
        downloaded = episode_status_quality(line).get('quality')

        if quality in alowed and quality not in preferred and quality > downloaded:
            candidates.append(filter_for_status(line))

        if quality in preferred and quality > downloaded:
            download_list.append(filter_for_status(line))
    adding_to_download_candidate_lists(line+1)

def find_best_allowed(x, y): # x, y [0] is the title + episode; x, y [2] is the quality_int
    if x[0] == y[0] and x[0] not in download_list:
        if x[2] > y[2]:
            return x
        else:
            return y
    elif x != y and not x in download_list:
            download_list.append(x)
            return y
    else:
        return y

def add_torrents_to_transmission(torrent: int):
    if len(download_list) > torrent:
        transmission_rpc.add_torrent(download_list[torrent][6])
    else:
        return
    add_torrents_to_transmission(torrent+1)

adding_to_download_candidate_lists(0)

reduce(find_best_allowed, candidates)

print(sorted(download_list))

add_torrents_to_transmission(0)
