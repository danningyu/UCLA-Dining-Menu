from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
from enum import Enum
from datetime import date, datetime
from apscheduler.schedulers.blocking import BlockingScheduler
import collections

sched = BlockingScheduler()
TEST_URL = 'http://menu.dining.ucla.edu/Menus'

meal_period_key = {0:'Breakfast', 1:'Lunch', 2:'Dinner'}
dining_hall_key = {0:'Covel', 1:'De Neve', 2:'Feast', 3:'Bruin Plate'}

def simple_get(url):
	print('Downloading content from menu webpage...')
	try:
		with closing(get(url, stream=True)) as resp:
			if is_good_response(resp):
				print('Successfully downloaded page.')
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

Items_And_Date = collections.namedtuple('Items_And_Date', ['items', 'date'])

def separate_by_meal_period(html_file):
	#takes in html page, and places menu items in appropriate list
	#returns list of lists, one list for each meal period
	soup = BeautifulSoup(html_file, 'html.parser')
	dates_and_items = soup.find_all(['h2', 'h3', 'a']) #h2 for date, a for menu items
	# print(dates_and_items)
	for num, item in enumerate(dates_and_items):
		print(str(num) + str(item))
	breakfast_items = []
	lunch_items = []
	brunch_items = []
	dinner_items = []
	food_items = [breakfast_items, brunch_items, lunch_items, dinner_items]
	dates_and_items = dates_and_items[41:] #eliminate headers
	dates_and_items = dates_and_items[:-5] #and footers
	index=-1
	date_time_obj = None
	for link in dates_and_items:
		if(link.contents[0].find(' for ') != -1):
		#need spaces, otherwise fails on words like "California"
			contains_date = link.contents[0]
			menu_date = contains_date[contains_date.find(',')+2:]
			date_time_obj = datetime.strptime(menu_date, '%B %d, %Y')
			print('Extracted date: ' + str(date_time_obj))
		if any('Detailed Breakfast' in s for s in link):
			index = 0
		elif any('Detailed Brunch' in s for s in link):
			index = 1
		elif any('Detailed Lunch' in s for s in link):
			index = 2
		elif any('Detailed Dinner' in s for s in link):
			index = 3
		food_items[index].append(link.contents[0]+'\n')
	return_val = Items_And_Date(food_items, date_time_obj)
	return return_val

def export_data():
	print('Running program...')
	current_day = date.today()
	current_time = datetime.now().time()
	output = simple_get(TEST_URL) #get the webpage
	# print(output)
	print('Exporting data...')
	all_items_and_date = separate_by_meal_period(output)
	all_items = all_items_and_date[0]
	#for meal_period_items in all_items_and_date[0]:
		#add_locations(meal_period_items)

	filename = "menu.txt"
	file1 = open(filename, "w+")
	file1.writelines('UCLA Dining menu for ' + str(current_day) + '\n')
	file1.writelines('Generated on PDT\n\n')
	file1.writelines(all_items[0])
	file1.write('\n\n')
	file1.writelines(all_items[1])
	file1.write('\n\n')
	file1.writelines(all_items[2])
	file1.write('\n\n')
	file1.writelines(all_items[3])
	file1.close()
	print('Done running program...')

#run once upon startup
export_data()

@sched.scheduled_job('interval', seconds=600)
def timed_job():
    print('Executing job on ' + str(datetime.now().time()))
    export_data()

sched.start()