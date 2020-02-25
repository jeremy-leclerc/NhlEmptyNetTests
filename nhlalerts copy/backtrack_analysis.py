import json
from get_caches_requests import cached_get_request

def get_games(start_date, end_date):
	"""
	start and end date are strings
	returns json content Game objects
	"""

	webpath = "https://statsapi.web.nhl.com/api/v1/schedule?startDate=" + start_date + "&endDate=" + end_date
	return cached_get_request(webpath)


def get_gameplay_by_id(game_id):
	"""
	game id is an int
	returns the Gameplay object
	"""

	game_webpath = "https://statsapi.web.nhl.com/api/v1/game/" + str(game_id) +"/feed/live"
	return cached_get_request(game_webpath)

# def get_plays(gameplay):
# 	"""
# 	gameplay is a Gameplay object
# 	returns all the plays within the gameplay
# 	"""
# 	return game_content_json["liveData"]["plays"]

def get_backtest_plays_data(start_date, end_date):

	games = []
	game_dates = get_games(start_date, end_date)["dates"]
	for date in game_dates:
		for schedule_game in date["games"]:
			game_play = get_gameplay_by_id(schedule_game["gamePk"])
			games.append({
				"date": date["date"],
				"game_id": schedule_game["gamePk"],
				"home_team_id": schedule_game["teams"]["home"]["team"]["id"],
				"away_team_id": schedule_game["teams"]["away"]["team"]["id"],
				"home_team_name": schedule_game["teams"]["home"]["team"]["name"],
				"away_team_name": schedule_game["teams"]["away"]["team"]["name"],
				"home_score": schedule_game["teams"]["home"]["score"],
				"away_score": schedule_game["teams"]["away"]["score"],
				"game_play": game_play
			})

	return games






