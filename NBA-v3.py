import pandas as pd
import numpy as np
import datetime as dt
import lightgbm as lgb
import streamlit as st
import ast
import os
from PIL import Image

#setting file paths
here = os.path.dirname(os.path.abspath(__file__))
filename = os.path.join(here, 'NBA2020_21df_fullseason_fullnames.csv')

filename2 = os.path.join(here, 'NBA2021_22df_fullnames.csv')

model_name =  os.path.join(here, 'NBA21_436rmse_PTS_fullname.txt')
model_name_AST =  os.path.join(here, 'NBA_AST_rmse_095_fullnames.txt')
model_name_3pt =  os.path.join(here, 'NBA21_0_61rmse_3pts_fullname.txt')

# image = Image.open('basketball.png')

# NBA2021df = pd.read_csv(filename) #used for later season

#used for early season
NBA2020df = pd.read_csv(filename)
df2 = pd.read_csv(filename2)
dfs = [NBA2020df, df2]
# NBA2021df = pd.concat(dfs) #change after early weeks
NBA2021df = df2.copy() #changed


true_cols = ['dup', 'Rk', 'Num_Game', 'Date', 'Age', 'Tm', 'Home', 	'Opp', 'Result',  'GS',	'Mins', 'FG',	'FGA',	'FGPct', '3P',	'3PA',	'3PPct',
             'FT',	'FTA',	'FTPct', 'ORB', 'DRB',	'TotRBs', 'AST', 'STL', 'BLK', 'TOV', 'PFouls', 'PTS',	'GmSc', '+/-', 'Player']
NBA2021df.columns = true_cols

# today = pd.to_datetime('2021-05-16') #used as place marker before season begins
today = pd.to_datetime(dt.date.today())
start_date =  today - dt.timedelta(weeks=2) #change to include desired timeline for avg

# to_drop = ['dup', 'Age', 'Result'] old drops
# NBA2021df.drop(to_drop, axis=1, inplace=True)
# to_fillna = ['Num_Game', 'FGPct', '3PPct', 'FTPct', '+/-'] old fills

to_fillna = ['Num_Game', 'FGPct', '3PPct', 'FTPct', 'TOV', 'PFouls', 'PTS', 'Player', 'GmSc'] #new fills
NBA2021df[to_fillna] = NBA2021df[to_fillna].fillna(0)

player_dict = dict(zip(NBA2021df.Player, NBA2021df.Tm)) #make player to team dict

NBA2021df = NBA2021df[~NBA2021df.Tm.str.contains('Tm')]
NBA2021df = NBA2021df[~NBA2021df.GS.str.contains('Inactive')]
NBA2021df = NBA2021df[~NBA2021df.GS.str.contains('Not')]

Wlist = ['W'] #prepare Result col for inference
NBA2021df['Result'] = NBA2021df['Result'].apply(lambda x: 1 if x[0] in Wlist else 0)

NBA2021df['Mins'] = NBA2021df['Mins'].str.replace(r':', '.')
NBA2021df['Home'] = [0 if r=='@' else 1 for r in NBA2021df['Home']]

NBA2021df['Date'] = pd.to_datetime(NBA2021df['Date'], format='%Y-%m-%d', errors='coerce')
X_val = NBA2021df[(NBA2021df['Date'] > start_date) & (NBA2021df['Date'] <= today)].copy()


stats_cols = ['Num_Game', 'Result', 'Mins',  'FG', 'Home', 'FGA', 'FGPct', '3P', '3PA', '3PPct',	
              'FT',	'FTA',	'FTPct', 'ORB', 'DRB', 'TotRBs', 'AST',	'STL', 'TOV', 'PFouls',	'PTS', 'GmSc', 'BLK', '+/-']

NBA2021df[stats_cols] = NBA2021df[stats_cols].apply(pd.to_numeric)
X_val[stats_cols] = X_val[stats_cols].apply(pd.to_numeric)


NBA2021df.set_index('Player', inplace=True)
NBA2021df.reset_index(inplace=True)

# player_dict = dict(zip(NBA2021df.Player, NBA2021df.Tm))


file = open("games_dict_home.txt", "r")
game_dict = file.read()
game_dict_home = ast.literal_eval(game_dict)

file = open("games_dict_visit.txt", "r")
game_dict_2 = file.read()
game_dict_visit = ast.literal_eval(game_dict_2)

file.close()


X_val = X_val.dropna(subset=['Player'])
X_val = X_val[X_val.Player.str.contains('https://www.basketball-reference.com/contracts') == False]
# X_val[stats_cols] = X_val[stats_cols].apply(pd.to_numeric)
X_val = X_val.groupby('Player').agg([np.average]).round(0)
X_val = X_val.reset_index()


today_df = pd.DataFrame()

today_df["Player"] = X_val['Player'].copy()
today_df[stats_cols] = X_val[stats_cols].copy()
today_df['Tm'] = today_df['Player'].map(player_dict)
today_df['Opp'] = today_df['Tm'].map(game_dict_visit)
today_df['Opp'] = np.where(today_df['Opp'].isna(), today_df['Tm'].map(game_dict_home), today_df['Tm'].map(game_dict_visit))
today_df['Date'] = pd.to_datetime(NBA2021df['Date'], infer_datetime_format=True, errors='coerce')

today_df = today_df.dropna(subset=['Opp'])
today_df = today_df.drop_duplicates(subset=['Player'])


order_cols = ['Player', 'Num_Game', 'Tm', 'Home', 'Opp', 'Result',
       'Mins', 'FG', 'FGA', 'FGPct', '3P', '3PA', '3PPct', 'FT', 'FTA',
       'FTPct', 'ORB', 'DRB', 'TotRBs', 'AST', 'STL', 'BLK', 'TOV', 'PFouls',
       'PTS', 'GmSc', '+/-'] #new order

today_df = today_df[order_cols]

today_df.set_index('Player', inplace=True)
today_df.reset_index(inplace=True)

today_df = today_df[(today_df.Mins > 12) & (today_df['PTS'] > 5)].copy() #adjust mins as needed
# today_df.drop('Date', axis=1, inplace=True)


today_df = today_df[~today_df.Player.str.contains('p/pettibo01|a/abdulka01|i/iversal01|k/kiddja01|s/stockjo01|w/westje01|o/olajuha01|h/hayesel01|d/duncati01|c/cousybo01|Page Not')]
today_df = today_df[~today_df.Player.str.contains('b/birdla01|b/bryanko01|n/nowitdi01|r/russebi01|m/malonka01|r/robinda01|s/schaydo01|t/thomais01|a/arizipa01|b/bayloel01')]
today_df = today_df[~today_df.Player.str.contains('o/onealsh01|w/wadedw01|r/roberos01|j/johnsma02|g/garneke01|m/malonmo01|j/jordami01|b/barklch01|c/chambwi01|h/havlijo01')]
today_df = today_df[~today_df.Player.str.contains('Hakeem Olajuwon|John Stockton|Wilt Chamberlain|Elvin Hayes|Dolph Schayes|John Havlicek|j/jordami01|b/barklch01|c/chambwi01|h/havlijo01')]

to_drop_PTS = ['Result', 'BLK', '+/-', 'PTS', 'Home'] #new drops .44rmse_PTS_fullnames
to_drop_AST = ['Result', 'DRB', 'Num_Game', 'AST', 'Home']
# to_drop_3pt = ['Result', 'BLK', 'ORB', 'Num_Game', '3P'] old drops
to_drop_3pt = ['Result', 'BLK', 'ORB', 'Num_Game', 'Home', '3PPct', '3PA', '3P']

NBA_regmodel = lgb.Booster(model_file=model_name)
NBA_regmodel_AST = lgb.Booster(model_file=model_name_AST)
NBA_3pt_classmod = lgb.Booster(model_file=model_name_3pt)

# X_today = today_df.drop('PTS', axis=1).copy()
X_today = today_df.drop(to_drop_PTS, axis=1).copy()
X_today['Tm'] = X_today['Tm'].astype('category')
X_today['Opp'] = X_today['Opp'].astype('category')
X_today['Player'] = X_today['Player'].astype('category')

y_today = today_df['PTS'].copy()

# #assist model inference prep
# X_ast = today_df.drop('AST', axis=1).copy() #old drop
X_ast = today_df.drop(to_drop_AST, axis=1).copy()
X_ast['Tm'] = X_ast['Tm'].astype('category')
X_ast['Opp'] = X_ast['Opp'].astype('category')
X_ast['Player'] = X_ast['Player'].astype('category')

y_ast = today_df['AST'].copy()

#3pt model inference prep
X_3pt = today_df.drop(to_drop_3pt, axis=1).copy()
X_3pt['Tm'] = X_3pt['Tm'].astype('category')
X_3pt['Opp'] = X_3pt['Opp'].astype('category')
X_3pt['Player'] = X_3pt['Player'].astype('category')

y_3p = today_df['3P'].copy()


#model inference
preds_today = NBA_regmodel.predict(X_today, categorical_feature=['Tm', 'Opp', 'Player']).round(0)
AST_preds_today = NBA_regmodel_AST.predict(X_ast, categorical_feature=['Tm', 'Opp', 'Player']).round(0)
three_preds_today = NBA_3pt_classmod.predict(X_3pt, categorical_feature=['Tm', 'Opp', 'Player']).round()

#dataframe with predictions per player
players_today = pd.DataFrame()
players_today['Player'] = X_today['Player'].copy()
players_today['Tm'] = X_today['Tm'].copy()
players_today['Pred_PTS'] = preds_today.copy()
players_today['Pred_AST'] = AST_preds_today.copy()
players_today['3pt'] = three_preds_today.copy()

team_totals = pd.DataFrame()
team_totals = players_today.groupby(['Tm']).sum()
team_totals.reset_index(inplace=True)
team_points_dict = dict(zip(team_totals.Tm, team_totals.Pred_PTS))


#final dataframe
to_deliver_df = pd.DataFrame()
to_deliver_df['Home_Team']  = today_df['Tm'].unique()
to_deliver_df['Away_Team']  = to_deliver_df['Home_Team'].map(game_dict_home)
to_deliver_df = to_deliver_df.drop_duplicates()
to_deliver_df = to_deliver_df.dropna()
to_deliver_df['Predicted_Home_Pts'] = to_deliver_df['Home_Team'].map(team_points_dict)
to_deliver_df['Predicted_Away_Pts'] = to_deliver_df['Away_Team'].map(team_points_dict)
to_deliver_df['Predicted_Total'] = to_deliver_df['Predicted_Home_Pts'] + to_deliver_df['Predicted_Away_Pts']

#fantasy prediction
players_today['Fantasy_Score'] = (((players_today['Pred_PTS'] * 1 - (players_today['3pt'] * 3)) + players_today['Pred_AST'] * 1.5 +
                            players_today['3pt'] * 3) * 0.85)

# making logos df
file = open("NBA_logos_dict.txt", "r")
logos_dict = file.read()
logos_dict_r = ast.literal_eval(logos_dict)

def path_to_image_html(path):
    return '<img src="'+ path + '" width="65" >'  
    
logo_df = to_deliver_df.copy().reset_index(drop=True)
logo_df['Home_Team'] = logo_df['Home_Team'].map(logos_dict_r)
logo_df['Away_Team'] = logo_df['Away_Team'].map(logos_dict_r)

#streamlit stuff
# st.image(image, width=80)
st.write("""
       ### **Predictions are called per player then grouped per team. Does not take into account injuries or specific player-player matchups.**
       """)
st.text("")

st.write("""
        #### **For capping games: Subtract the predicted score for an injured/resting player from the team total to get a more accurate team score.**
	""")
st.text("")
st.text("")

# main game predictions df siaplayed as HTML object
st.markdown(logo_df.to_html(escape=False, formatters=dict(Home_Team=path_to_image_html,  Away_Team=path_to_image_html)), unsafe_allow_html=True)
st.text("")
st.text("")
st.text("")
st.text("")

# box to search players by name
user_input_player = st.text_input("Search players by name in the field below")
if user_input_player:
	per_player = pd.DataFrame(players_today[players_today['Player'].str.contains(str(user_input_player.title()))])
	st.write(per_player.astype('object'))
st.text("")

# top fantasy scorer box
m = max(players_today['Fantasy_Score'])
awesomeness_enabled = st.checkbox('Top Fantasy Performer')
if not awesomeness_enabled:
   pass
else:
       st.markdown(players_today[players_today['Fantasy_Score'] == m].to_html(escape=False, formatters=dict(Home_Team=path_to_image_html,  Away_Team=path_to_image_html)), unsafe_allow_html=True)
st.text("")
st.text("")
st.text("")
st.text("")


#per team stats breakdown box
user_input_team = st.text_input("Enter team name abbreviation (from sidebar dropdown) for per team, per player breakdown")

if user_input_team:
	per_team = pd.DataFrame(players_today[players_today['Tm'].str.contains(str(user_input_team.upper()))])
	st.write(per_team.astype('object'))

#team abbrev info sidebar
teams_list =  NBA2021df.Tm.drop_duplicates().reset_index().drop('index', axis=1)
with st.sidebar.expander("Team Abbreviations"):
       teams_list
