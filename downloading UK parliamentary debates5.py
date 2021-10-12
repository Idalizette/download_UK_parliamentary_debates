import urllib.request
from bs4 import BeautifulSoup
import os
from multiprocessing import Pool

def open_link_with_exceptions(link):
	"""opens a link. When there are connection issues, it doesn't crash the programme, but does a timeout and tries again"""
	try:
		f = urllib.request.urlopen(link)
	except urllib.error.HTTPError:
		writing = f"{link} \n"
		with open("these URLs don't exist.txt", 'a') as f:
			f.write(writing)
			return False
	except (urllib.error.URLError, ConnectionResetError, ConnectionAbortedError, TimeoutError):
		print("TIME-OUT")
		starttime = mytime()
		times = []
		print(mytime())
		while mytime()-starttime < 20:
			if mytime() - starttime % 1000 == 0 and mytime() not in times:
				print(mytime())
				times.append(mytime())
		f = urllib.request.urlopen(link)
	
	myfile = f.read()
	return myfile

def debates_for_a_day(year, month, daynumber):
	"""looking at the index page for each date, to find the urls of all the debates that day"""
	urls_lords = []
	urls_commons = []
	date = f"{year}/{month}/{daynumber}"
	link = f"https://api.parliament.uk/historic-hansard/sittings/{date}"
	myfile = open_link_with_exceptions(link)
	rawtext = myfile.decode('UTF-8')

	#finding the urls for that day
	for i in range(0, len(rawtext)):
		if rawtext[i:i+19] == f"commons/{date}":
			urlstart = i
			for j in range(i,i+100):
				if rawtext[j:j+2] == '">':
					urlend = j
			url = f"https://api.parliament.uk/historic-hansard/{rawtext[urlstart:urlend]}"
			urls_commons.append(url)
		if rawtext[i:i+17] == f"lords/{date}":
			urlstart = i
			for j in range(i,i+100):
				if rawtext[j:j+2] == '">':
					urlend = j
			url = f"https://api.parliament.uk/historic-hansard/{rawtext[urlstart:urlend]}"
			urls_lords.append(url)

	return urls_commons, urls_lords

def clean_debate(link):
	"""removes unwanted text from a debate"""
	print(link)
	myfile = open_link_with_exceptions(link)
	if myfile == False:
		return False
	soup = BeautifulSoup(myfile,'html.parser')
	text_topic = soup.get_text()
	text_topic = text_topic.replace("Search Help", "")
	text_topic = text_topic.replace("Noticed a typo? | Report other issues | © UK Parliament", "")

	for i in range(4, len(text_topic)):
		if text_topic[i] == " ":
			title_end = i
			break
	title = text_topic[4:title_end]
	while "   " in text_topic:
		text_topic = text_topic.replace("   ", " ")
	while "\n\n" in text_topic:
		text_topic = text_topic.replace("\n\n", "\n")
	for i in range (title_end, i + len(text_topic)):
		if text_topic[i:i+len(title)] == title:
			start_relevant = i
			break
	text_topic = text_topic[start_relevant:len(text_topic)]

	info_line = text_topic.split("\n")[1]
	i = len(info_line)-1
	#if there's multiple columns
	removething = ""
	if "cc" in info_line:
		start_column = False
		end_column = False
		hyphen = False
		while i > 0:
			if info_line[i] == "-":
				hyphen = i
				end_column = info_line[i+1:len(info_line)+1]
			elif info_line[i] == "c":
				start_column = info_line[i+1:hyphen]
				break
			i -= 1
		if end_column.isdigit() and start_column.isdigit(): #sometimes there's a typo on the website, where the column isn't a number but a letter, which would crash the code
			if int(end_column) < int(start_column):
				if len(start_column)-len(end_column) == 1:
					end_column = f"{start_column[0]}{end_column}"
				if len(start_column)-len(end_column) == 2:
					end_column = f"{start_column[0:2]}{end_column}"
				if len(start_column)-len(end_column) == 3:
					end_column = f"{start_column[0:3]}{end_column}"
				if len(start_column)-len(end_column) == 4:
					end_column = f"{start_column[0:4]}{end_column}"

			columns = list(range(int(start_column), int(end_column)+1))

			for column in columns:
				if f" {column}\n" in text_topic:
					removething = f" {column}\n"
				elif f"\n{column}\n" in text_topic:
					removething = f"\n{column}\n"
				else:
					removething = ""

				text_topic = text_topic.replace(removething, "")
	
	#if there's just the one column
	elif "c" in info_line:
		while i > 0:
			if info_line[i] == "c":
				column = info_line[i+1:len(info_line)+1]
				break
			i -= 1
		if f" {column}\n" in text_topic:
			removething = f" {column}\n"
		elif f"\n{column}\n" in text_topic:
			removething = f"\n{column}\n"

		text_topic = text_topic.replace(removething, "")

	if "-\n" in text_topic:
		text_topic = text_topic.replace("-\n", "")


	return text_topic

def download_sitting(urls, file_name):
	"""downloads all the text in the sittings in the urls list, and saves them under the name file_name"""
	text_sitting_string = ""
	text_sitting_list = (my_pool.map(clean_debate, urls))
	for text_topic in text_sitting_list:
		if text_topic:
			text_sitting_string = f"{text_sitting_string}{text_topic}"
	file_name = f"{file_name}.txt"
	with open(file_name, 'w', encoding = "utf8") as f:
		f.write(text_sitting_string)

if __name__ == "__main__":
	years = list(range(1803, 2006))
	months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
	daynumbers = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30','31']
	daynumbers_int = list(range(1,32))
	path = "C:/Users/idali/OneDrive/Documents/Parliamentary Debates UK"
	my_pool = Pool()
	#we will want to check whether we've already downloaded this file, so here's a list of everything we've downloaded so far
	files_files = os.listdir(path)
	files_files_commons = [file[0:26] for file in files_files]
	files_files_lords = [file[0:24] for file in files_files]
	files_files_0_10 = [file[0:10] for file in files_files]
	files_files_0_7 = [file[0:7] for file in files_files]
	files_files_0_5 = [file[0:5] for file in files_files]


	for year in years:
		print(year)
		#we only look at months that debates actually took place in
		actual_months = []
		link = f"https://api.parliament.uk/historic-hansard/sittings/{year}/index.html"
		myfile = open_link_with_exceptions(link)
		if myfile:
			rawtext = myfile.decode('UTF-8')
		else:
			continue

		for month in months:
			if rawtext.count(month) > 1: #months that don't have debates behind them only appear in the page source once
				actual_months.append(month)
		
		print(actual_months)
		for month in actual_months:
			print(month)
			month_number = months.index(month)+1
			month_number = str(month_number)
			if len(month_number) == 1:
				month_number = f"0{month_number}"
			#we only look at days that debates actually took place in
			actual_daynumbers = []
			link = f"https://api.parliament.uk/historic-hansard/sittings/{year}/{month}/index.html"
			print(link)
			myfile = open_link_with_exceptions(link)
			rawtext = myfile.decode('UTF-8')
			for daynumber in daynumbers_int:
				if len(str(daynumber)) == 1:
					if f">{daynumber}</a></td>" in rawtext: #this is only in the page source if there's a link
						actual_daynumbers.append(f"0{daynumber}")
				elif len(str(daynumber)) == 2:
					if f"{daynumber}</a></td>" in rawtext: #this is only in the page source if there's a link
						actual_daynumbers.append(str(daynumber))
			for i in range(0,len(actual_daynumbers)): #we're doing this with i, cuz that will allow us to look at the previous one
				#now we're actually starting on the actual webpages
				daynumber = actual_daynumbers[i]

				urlsdate_commons, urlsdate_lords = debates_for_a_day(year, month, daynumber) #we have two lists of output in our function
				if urlsdate_commons: #there might be lords sittings but no commons sittings on a day, in that case this list is empty and this if statement is False
					file_name = f"{year}-{month_number}-{daynumber} Commons Sitting"
					if file_name in files_files_commons:
						print(f"{file_name} already downloaded")
					else:
						print("downloading", file_name)

						download_sitting(urlsdate_commons, file_name)

				if urlsdate_lords:
					file_name = f"{year}-{month_number}-{daynumber} Lords Sitting"
					if file_name in files_files_lords:
						print(f"{file_name} already downloaded")
					else:
						print("downloading", file_name)
						download_sitting(urlsdate_lords, file_name)