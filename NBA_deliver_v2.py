import pandas as pd
import numpy as np
import datetime as dt
import lightgbm as lgb
import streamlit as st
import ast
import os
from PIL import Image


here = os.path.dirname(os.path.abspath(__file__))
filename = os.path.join(here, 'NBA2020_21df.csv')

filename2 = os.path.join(here, 'NBA2020_21df_fullseason')

model_name =  os.path.join(here, 'NBA_PTS_REG_MODEL_v4.txt')
model_name_AST =  os.path.join(here, 'NBA_AST_REG_MODEL_v1.txt')
image = Image.open('basketball.png')



# url2 = 'NBA2020_21df.csv'
NBA2020df = pd.read_csv(filename)
df2 = pd.read_csv(filename2)

dfs = [NBA2019df, NBA2020df]
NBA2021df = pd.concat(dfs) #change after early weeks


true_cols = ['dup', 'Rk', 'Num_Game',	'Date',	'Age',	'Tm', 'Home', 	'Opp', 'Result',	 'GS',	'Mins',	'FG',	'FGA',	'FGPct',	'3P',	'3PA',	'3PPct',
             'FT',	'FTA',	'FTPct',	'ORB', 'DRB',	'TotRBs',	'AST',	'STL',	'BLK',	'TOV',	'PFouls',	'PTS',	'GmSc',	'+/-', 'Player']
NBA2021df.columns = true_cols

today = pd.to_datetime('2021-05-16') #used as place marker before season begins
# today = pd.to_datetime(dt.date.today())
start_date =  today - dt.timedelta(weeks=2.5)

to_drop = ['dup', 'Age', 'Result']
NBA2021df.drop(to_drop, axis=1, inplace=True)

to_fillna = ['Num_Game', 'FGPct', '3PPct', 'FTPct', '+/-']
NBA2021df[to_fillna] = NBA2021df[to_fillna].fillna(0)

NBA2021df = NBA2021df[~NBA2021df.Tm.str.contains('Tm')]
NBA2021df = NBA2021df[~NBA2021df.GS.str.contains('Inactive')]
NBA2021df = NBA2021df[~NBA2021df.GS.str.contains('Not')]

NBA2021df['Mins'] = NBA2021df['Mins'].str.replace(r':', '.')
NBA2021df['Home'] = [0 if r=='@' else 1 for r in NBA2021df['Home']]

NBA2021df['Date'] = pd.to_datetime(NBA2021df['Date'], format='%Y-%m-%d', errors='coerce')
X_val = NBA2021df[(NBA2021df['Date'] > start_date) & (NBA2021df['Date'] <= today)].copy()
NBA2021df['Date'] = NBA2021df['Date'].apply(lambda x: x.value)

stats_cols = ['Rk',	'Num_Game', 'Date', 'Home', 'GS',	'Mins',	'FG',	'FGA',	'FGPct',	'3P',	'3PA',	'3PPct',	
              'FT',	'FTA',	'FTPct',	'ORB',	'DRB',	'TotRBs',	'AST',	'STL',	'BLK',	'TOV',	'PFouls',	'PTS',	'GmSc',	'+/-']
NBA2021df[stats_cols] = NBA2021df[stats_cols].apply(pd.to_numeric)
NBA2021df.set_index('Player', inplace=True)
NBA2021df.reset_index(inplace=True)

player_dict = dict(zip(NBA2021df.Player, NBA2021df.Tm))



file = open("games_dict_home.txt", "r")
game_dict = file.read()
game_dict_home = ast.literal_eval(game_dict)

file = open("games_dict_visit.txt", "r")
game_dict_2 = file.read()
game_dict_visit = ast.literal_eval(game_dict_2)

file.close()



X_val = X_val.dropna(subset=['Player'])
X_val = X_val[~X_val.Player.str.contains('https://www.basketball-reference.com/contracts')]
X_val[stats_cols] = X_val[stats_cols].apply(pd.to_numeric)
X_val = X_val.groupby('Player').agg([np.average]).round(0)
X_val = X_val.reset_index()



today_df = pd.DataFrame()

today_df["Player"] = X_val['Player'].copy()
today_df[stats_cols] = X_val[stats_cols].copy()
today_df['Tm'] = today_df['Player'].map(player_dict)

today_df['Opp'] = today_df['Tm'].map(game_dict_visit)
today_df['Opp'] = np.where(today_df['Opp'].isna(), today_df['Tm'].map(game_dict_home), today_df['Tm'].map(game_dict_visit))

today_df['Date'] = pd.to_datetime(today_df['Date'], infer_datetime_format=True, errors='coerce')
today_df['Date'] = today
today_df = today_df.dropna(subset=['Opp'])
today_df = today_df.drop_duplicates(subset=['Player'])

order_cols = ['Player', 'Rk',	'Num_Game',	'Date',	'Tm',	'Home',	'Opp',	'GS',	'Mins',	'FG',	'FGA',	'FGPct',	
              '3P',	'3PA',	'3PPct',	'FT',	'FTA',	'FTPct',	'ORB',	'DRB',	'TotRBs',	'AST',	'STL',	'BLK',
              'TOV',	'PFouls',	'PTS',	'GmSc',	'+/-']
today_df = today_df[order_cols]
today_df['Date'] = today_df['Date'].apply(lambda x: x.value)

today_df = today_df[(today_df.Mins > 4.5) & (today_df['PTS'] > 5)].copy()

today_df = today_df[~today_df.Player.str.contains('p/pettibo01|a/abdulka01|i/iversal01|k/kiddja01|s/stockjo01|w/westje01|o/olajuha01|h/hayesel01|d/duncati01|c/cousybo01')]
today_df = today_df[~today_df.Player.str.contains('b/birdla01|b/bryanko01|n/nowitdi01|r/russebi01|m/malonka01|r/robinda01|s/schaydo01|t/thomais01|a/arizipa01|b/bayloel01')]
today_df = today_df[~today_df.Player.str.contains('o/onealsh01|w/wadedw01|r/roberos01|j/johnsma02|g/garneke01|m/malonmo01|j/jordami01|b/barklch01|c/chambwi01|h/havlijo01')]


NBA_regmodel = lgb.Booster(model_file=model_name)
NBA_regmodel_AST = lgb.Booster(model_file=model_name_AST)

X_today = today_df.drop('PTS', axis=1).copy()

X_today['Tm'] = X_today['Tm'].astype('category')
X_today['Opp'] = X_today['Opp'].astype('category')
X_today['Player'] = X_today['Player'].astype('category')

y_today = today_df['PTS'].copy()


#assist model inference prep
X_ast = today_df.drop('AST', axis=1).copy()
X_ast['Tm'] = X_ast['Tm'].astype('category')
X_ast['Opp'] = X_ast['Opp'].astype('category')
X_ast['Player'] = X_ast['Player'].astype('category')

y = today_df['AST'].copy()





preds_today = NBA_regmodel.predict(X_today, categorical_feature=['Tm', 'Opp', 'Player']).round(0)
AST_preds_today = NBA_regmodel_AST.predict(X_ast, categorical_feature=['Tm', 'Opp', 'Player']).round(0)



players_today = pd.DataFrame()
players_today['Player'] = X_today['Player'].copy()
players_today['Tm'] = X_today['Tm'].copy()
players_today['Pred_PTS'] = preds_today.copy()
players_today['Pred_AST'] = AST_preds_today.copy()


team_totals = pd.DataFrame()
team_totals = players_today.groupby(['Tm']).sum()
team_totals.reset_index(inplace=True)
team_points_dict = dict(zip(team_totals.Tm, team_totals.Pred_PTS))



to_deliver_df = pd.DataFrame()
to_deliver_df['Home_Team']  = today_df['Tm'].unique()
to_deliver_df['Away_Team']  = to_deliver_df['Home_Team'].map(game_dict_home)
to_deliver_df = to_deliver_df.drop_duplicates()
to_deliver_df = to_deliver_df.dropna()
to_deliver_df['Predicted_Home_Pts'] = to_deliver_df['Home_Team'].map(team_points_dict)
to_deliver_df['Predicted_Away_Pts'] = to_deliver_df['Away_Team'].map(team_points_dict)
to_deliver_df['Predicted_Total'] = to_deliver_df['Predicted_Home_Pts'] + to_deliver_df['Predicted_Away_Pts']

###streamlit stuff

st.image(image, width=120)

st.write("""
	## **Predictions are called per player then grouped per team. Does not take into account injuries or specific player-player matchups.**

	### **One idea for capping games: Take the predicted score for an injured/resting player and subtract from predicted team total to get a more accurate predicted team score.**
	""")



st.dataframe(to_deliver_df)







# m = players_today.Pred_PTS[players_today['Player'].str.contains('o/oubreke01')]
user_input_player = st.text_input("Enter player name(currently has to be in format 'o/oubreke01' from https://www.basketball-reference.com/)")


if user_input_player:
	per_player = pd.DataFrame(players_today[players_today['Player'].str.contains(str(user_input_player))])
	st.write(per_player.astype('object'))
# m







user_input_team = st.text_input("Enter team name abbreviation for per team, per player breakdown (must be playing today)")
st.write("""
	**Charlotte = CHO**

	**Phoenix = PHO**



	*Abbreviations are from https://www.basketball-reference.com/. Proper player names coming soon...*

	""")

if user_input_team:
	per_team = pd.DataFrame(players_today[players_today['Tm'].str.contains(str(user_input_team))])
	st.write(per_team.astype('object'))
# per_team