import urllib.request
import json
import hashlib

def cached_get_request(url):

	hashed_url = hashlib.sha1(url.encode('utf-8')).hexdigest()
	file_name = 'cached-requests/' + hashed_url + '.json'

	file_exists = True
	try:
		f = open(file_name)
	except IOError:
		file_exists = False

	if not file_exists:
		print("cached_get_request fetching ", url)
		content = urllib.request.urlopen(url).read()
		content_json = json.loads(content)
		f = open(file_name, "w+")
		f.write(json.dumps(content_json))
		f.close()

	f = open(file_name, "r")
	read_stuff = f.read()
	file_contents = json.loads(read_stuff)
	f.close()

	return file_contents


