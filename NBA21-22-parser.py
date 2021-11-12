from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import requests
from random import randint
from time import sleep
import datetime as dt
import ast
from selenium import webdriver

chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument("--disable-gpu")
driver =webdriver.Chrome('chromedriver',chrome_options=chrome_options)

main_url = 'https://www.basketball-reference.com/leagues/NBA_2022_per_game.html' #change year

links = []
driver.get(main_url) 
sleep(randint(3,10))
elems = driver.find_elements_by_tag_name('a')
for elem in elems:
  href = elem.get_attribute('href')
  if href is not None:
    links.append(href)

player_links = []
for i in links:
  string = 'player'
  if string in i:
    player_links.append(i) 

no_go = ['/players,','/players/injuries.htm','/players/salary.htm', '/players/uniform.cgi','https://www.basketball-reference.com/contracts/players','https://www.basketball-reference.com/gleague/players/',
         'https://www.basketball-reference.com/international/players/','https://www.basketball-reference.com/nbl/players/','https://www.basketball-reference.com/wnba/players/', 'https://www.basketball-reference.com/contracts/players']
list1 = [ele for ele in player_links if ele not in no_go] 

new_set =[x.replace('https://www.basketball-reference.com/players/', '').replace('.html', '') for x in list1[1:]]

table = []
for l in new_set:
    sleep(randint(3,7))
    main_url2 = 'https://www.basketball-reference.com/players/'
    driver.get(main_url2+str(l)+'/gamelog/2022') #change year
    info = driver.page_source
    try:
      soup = pd.read_html(info)
    except:
      pass
    df = soup[7:8]
    df = pd.concat(df) #don't concat
    name = driver.find_element_by_tag_name("h1").text #finds name
    name = name[0:-17] #display name only
    df['Player'] =  str(name)
    table.append(df)

NBAdf2021 = pd.concat(table)
NBAdf2021.to_csv('D:/Documents/ML_DOCS/ML Project Files/NBA_prjct_v1/NBA2021_22df_fullnames.csv')


##schedule parser + today's games dict created
main_url_sched = 'https://www.basketball-reference.com/leagues/NBA_2022_games-november.html' #update per month
driver.get(main_url_sched)
sleep(randint(3,8))
info = driver.page_source
soup = pd.read_html(info)
# df_sched = soup[0:1]
df_sched = pd.concat(soup)

sched_cols = ['Date',	'Start', 	'Visitor',	'PTS_vis',	'Home_team',	'PTS_home',	'box',	'dup1',	'Attend',	'Notes']
df_sched.columns = sched_cols
df_sched = df_sched[['Date', 'Visitor', 'Home_team']]
df_sched = df_sched[~df_sched.Visitor.str.contains('Visitor')]

team_name_dict = {'GSW':'Golden State Warriors', 'CLE':'Cleveland Cavaliers', 'DEN':'Denver Nuggets', 'MIA':'Miami Heat', 'NOP':'New Orleans Pelicans',
                  'SAS':'San Antonio Spurs', 'PHO':'Phoenix Suns', 'MEM':'Memphis Grizzlies', 'BRK':'Brooklyn Nets', 'MIL':'Milwaukee Bucks', 'LAL':'Los Angeles Lakers', 'POR':'Portland Trail Blazers', 
                  'ORL':'Orlando Magic', 'TOR':'Toronto Raptors', 'CHI':'Chicago Bulls', 'WAS':'Washington Wizards', 'UTA':'Utah Jazz', 'SAC':'Sacramento Kings', 'CHO':'Charlotte Hornets', 'NYK':'New York Knicks', 
                  'LAC':'Los Angeles Clippers', 'OKC':'Oklahoma City Thunder', 'MIN':'Minnesota Timberwolves', 'DET':'Detroit Pistons', 'ATL':'Atlanta Hawks', 'PHI':'Philadelphia 76ers', 
                  'IND':'Indiana Pacers','BOS':'Boston Celtics', 'HOU':'Houston Rockets', 'DAL':'Dallas Mavericks'}

team_name_dict_rev = dict(zip(team_name_dict.values(), team_name_dict.keys()))

df_sched['Visitor'] = df_sched['Visitor'].map(team_name_dict_rev)
df_sched['Home_team'] = df_sched['Home_team'].map(team_name_dict_rev)

not_days = ['Fri,', 'Sat,', 'Sun,', 'Mon,', 'Tue,', 'Wed,', 'Thu,']
today = pd.to_datetime(dt.date.today())

# today = pd.to_datetime('2021-10-19') #used as place marker before season begins
df_sched['Date'] = df_sched['Date'].str.replace(r'Fri,|Sat,|Sun,|Mon,|Tue,|Wed,|Thu', '')

##see if each month nees to be numerized
df_sched['Date'] = df_sched['Date'].str.replace(r'Jan', '01,') 

df_sched['Date'] = pd.to_datetime(df_sched['Date'], infer_datetime_format=True)
df_sched = df_sched[df_sched['Date'] == today].copy()

games_dict_home = dict(zip(df_sched.Home_team, df_sched.Visitor))
games_dict_visit = dict(zip(df_sched.Visitor, df_sched.Home_team))

save_path = 'D:/Documents/ML_DOCS/ML Project Files/NBA_prjct_v1/'
file_name = "games_dict_home.txt"
file_name_2 = "games_dict_visit.txt"
completeName1 = os.path.join(save_path, file_name)
completeName2 = os.path.join(save_path, file_name_2)

f1 = open(completeName1,"w")
f1.write( str(games_dict_home) )

f2 = open(completeName2,"w")
f2.write( str(games_dict_visit) )

f1.close()
f2.close()
driver.close()