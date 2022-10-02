# medusacsv 

A script that works with the [pymedusa api](https://medusaapi.docs.apiary.io/#), it downloads \
the torrents from a csv. \
Works for [csv's](https://github.com/arfonso01/Btdigcsv) with quotes and structure like ["serie","size","magnent"]

## Dependencies

- [python3](https://www.python.org/downloads/)
- [requests](https://pypi.org/project/requests/)
- [transmission-rpc](https://github.com/trim21/transmission-rpc/tree/v3.3.2)
- [transmissionbt](https://transmissionbt.com/)
- [pymedusa](https://pymedusa.com/)

## How to use it

- Step 1: Edit this variables (line 8-12):
		
		medusa_host = 'localhost:8081'
		medusa_api_key = 'your_api_key'
		transmission_rpc = Client(host='localhost', port=9091, username='myuser', password ='mypass')
		my_torrents_csv = 'torrents.csv'
		
		episode_format = 'Cap.\d+' # 's\d+e\d+' # '\d+x\d+'
		separator = '-' # after title, or '\(19\d+\)|\(20\d+\)' # year after title or 'other'

- Step 2: The lines 16, 17, 19 use use regex to find the quality, you can improve it:
		
		global_quality_format = '\w+\s\d+\w[i-p]|\w+\d+\w[i-p]|\d+\w[i-p]\s\w+|\d+\w[i-p]\w+|'
		UHD_quality_format = '4k\w+|4k\s\w+|\w+4k|\w+\s4k'

		quality_format = global_quality_format + UHD_quality_format

- Step 3: You can run the script
