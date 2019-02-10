#!/usr/bin/python
# coding=utf-8

# Ukrainian persident elections candidates' political program
# document metatata parser/dumper
#
# Copyright (C) 2019 George Kashperko (gkashperko[at]gmail.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied.  See the License for the specific language
# governing permissions and limitations under the License.


import sys
if 2 == sys.version_info.major:
	reload(sys)
	sys.setdefaultencoding('utf8')

import os, re, subprocess
if 2 < sys.version_info.major:
	from urllib.request import FancyURLopener
	from urllib.parse import urljoin
else:
	from urllib import FancyURLopener
	from urlparse import urljoin
from lxml import html

def urlopen(url):
	charset = None

	tmp = FancyURLopener()
	tmp = tmp.open(url)

	if 2 < sys.version_info.major:
		charset = tmp.info().get_content_charset()
	else:
		charset = 'windows-1251'

	tmp = tmp.read().decode(charset)
	if str != type(tmp):
		tmp = str(tmp.encode('utf-8'))

	return tmp

def download(who, url):
	tmp = FancyURLopener()
	url = tmp.open(url)
	if 2 < sys.version_info.major:
		path = url.info().get_filename()
	else:
		path = url.info().get('Content-Disposition').split('=')[1].strip('"')
	path = os.path.basename(path)
	with open(path, 'wb') as f:
		while True:
			tmp = url.read(4096)
			if 0 == len(tmp):
				break
			f.write(tmp)
		f.close()
	return path

def parseHtml(s):
	parser = html.HTMLParser(encoding = 'utf-8')
	return html.fromstring(s, parser = parser)

url = sys.argv[1]

# Load and parse candidates' list page
tmp = urlopen(url)
tree = parseHtml(tmp)

dump_pattern = re.compile('^(?P<key>[^:]+):(?P<value>.*)$')
dump_columns = [
	'who', 'date',
	'Author', 'Company',
	'Last Modified By', 'Last Printed',
	'Create Date', 'Modify Date',
]

def dump_csv(data):
	res = ''
	for tmp in dump_columns:
		v = data[tmp] if tmp in data else ''
		res += '"' + v + '",'

	print(res[:-1])

def dump(who, date, about, path):
	s = subprocess.Popen(
		['exiftool', '-dateFormat', '%F %T', path],
		stdout = subprocess.PIPE
	)

	data = {}
	while True:
		tmp = s.stdout.readline()
		if b'' == tmp:
			break

		try:
			m = dump_pattern.match(tmp.decode('utf-8'))
		except:
			continue

		data[m.group('key').strip()] = m.group('value').strip()
	s.wait()

	data.update({
		'who': who,
		'date': date,
	})

	dump_csv(data)

def parse_one(who, about, url):
	sys.stderr.write("Loading data for %s\n" % who)
	person = parseHtml(urlopen(url))
	doc = person.findall('body/table')[2].findall('tr/td[a="Передвиборна програма"]/a')[0]
	date = person.findall('body/table/tbody/tr[td="Дата рішення ЦВК про реєстрацію"]/td')[1].text
	path = download(who, urljoin(url, doc.attrib['href']))
	dump(who, date, about, path)

# Print header line
dump_csv({tmp: tmp for tmp in dump_columns})

# Iterate over candidates' entries in penultimate table
people = tree.findall('body/table')[-2]
for one in people.findall('tbody/tr'):
	rows = one.findall('td')
	one = rows[1].find('a')
	parse_one(one.text, rows[-1].text, urljoin(url, one.attrib['href']))
