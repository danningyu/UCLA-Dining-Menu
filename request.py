from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
from enum import Enum
from datetime import date, datetime
from apscheduler.schedulers.blocking import BlockingScheduler

sched = BlockingScheduler()
TEST_URL = 'http://menu.dining.ucla.edu/Menus'


meal_period_key = {0:'Breakfast', 1:'Lunch', 2:'Dinner'}
dining_hall_key = {0:'Covel', 1:'De Neve', 2:'Feast', 3:'Bruin Plate'}

def simple_get(url):
	try:
		with closing(get(url, stream=True)) as resp:
			if is_good_response(resp):
				return resp.content
			else:
				return None
	except RequestException as e:
		log_error('Error during requests to {0}:{1}'.format(url, str(e)))
		return None

def is_good_response(resp):
	content_type = resp.headers['Content-Type'].lower()
	return(resp.status_code==200 and content_type is not None 
		and content_type.find('html')>-1)

def log_error(e):
	print(e)

def process_data(html_file):
	soup = BeautifulSoup(html_file, 'html.parser')
	all_links = soup.find_all('a')
	i=0
	breakfast_items = []
	lunch_items = []
	dinner_items = []
	brunch_flag=False
	food_items = [breakfast_items, lunch_items, dinner_items]
	index = 0
	all_links = all_links[41:] #eliminate headers
	all_links = all_links[:-5] #and footers
	for link in all_links:
		i=i+1
		if any('Detailed Breakfast' in s for s in link):
			index = 0
			print('breakfast start')
		elif any('Detailed Lunch' in s for s in link):
			index = 1
			print('lunch start')
		elif any('Detailed Dinner' in s for s in link):
			index = 2
			print('dinner start')
		#if i<42:
		#	continue
		# print(str(i), end="")
		# print(link.contents)
		food_items[index].append(link.contents[0]+'\n')

	# for meal_items in food_items:
		# print(str('START'))
		# for items in meal_items:
			# print(str(items))
	
	return food_items
	# if len(breakfast_items) == 0 and len(lunch_items) != 0:
	#	brunch_flag = True
	#	print('No breakfast today, only brunch')

def add_locations(listOfItems, time):
	i=0
	index=0
	tempList = listOfItems.copy()
	if time == 0:	#breakfast	
		for items in tempList:
			if "Detailed Menu" in items and i==0:
				print('insert de neve')
				listOfItems.insert(index, '\n'+str(dining_hall_key[1])+'\n')
				i = i+1
			elif "Detailed Menu" in items and i==1:
				listOfItems.insert(index, '\n'+str(dining_hall_key[3])+'\n')
				i = i+1
			index = index+1
	elif time == 1 or time == 2:
		for items in tempList:
			if "Detailed Menu" in items:
				listOfItems.insert(index, '\n'+str(dining_hall_key[i])+'\n')
				i = i+1
			index = index+1

def export_data():
	current_day = date.today()
	current_time = datetime.now().time()
	output = simple_get(TEST_URL) #get the webpage
	all_items = process_data(output)
	current_time=str(current_time.hour)+'_'+str(current_time.minute)+'_'+str(current_time.second)
	time=0
	for meal_items in all_items:
		add_locations(all_items[time], time)
		time = time + 1
	filename = "menu"+current_time+".txt"
	file1 = open(filename, "w+")
	file1.writelines('UCLA Dining menu for ' + str(current_day) + '\n\n')
	file1.writelines('Generated on ' + str(current_time.replace('_', ':'))+ ' PDT\n')
	file1.writelines(all_items[0])
	file1.write('\n\n')
	file1.writelines(all_items[1])
	file1.write('\n\n')
	file1.writelines(all_items[2])
	file1.close()

@sched.scheduled_job('interval', seconds=1800)
def timed_job():
    print('Executing job on ' + str(datetime.now().time()))
    export_data()

sched.start()