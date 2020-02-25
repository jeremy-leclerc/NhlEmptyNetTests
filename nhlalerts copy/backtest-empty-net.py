import urllib.request
import json
from datetime import datetime
from get_caches_requests import cached_get_request

BET_SPREAD = 2

# def cached_get_request(url):
# 	hashed_url = hashing_function(url)
# 	if hashed_url file exists:
# 		return read(hashed_url)
# 	response = fetch(url)
# 	save(response)
# 	return response

def was_target_spread(spread):
	return spread == BET_SPREAD

def was_betting_enabled(game_time):
	return game_time > (3*60+30)

def is_near_end_of_game(game_time):
	return game_time < (5 * 60 + 30)

def would_have_placed_bet(spread_at_last_goal, time_at_last_goal, current_time_remaining):
	return was_target_spread(spread_at_last_goal) and \
		was_betting_enabled(time_at_last_goal) and \
		is_near_end_of_game(current_time_remaining)

webpath = "https://statsapi.web.nhl.com/api/v1/schedule?startDate=" + "2019-01-04" + "&endDate=" + "2019-12-27"

content_json = cached_get_request(webpath)

game_info_list = []

date_list = content_json["dates"]
for date in date_list:

	game_list = date["games"]
	for game in game_list:

		game_info_list.append({
			"date": date["date"],
			"game_id": game["gamePk"],
			"home_score": game["teams"]["home"]["score"],
			"away_score": game["teams"]["away"]["score"]
		})

count_bets = 0
count_success = 0

for game_info in game_info_list:
	
	game_id = game_info["game_id"]
	game_webpath = "https://statsapi.web.nhl.com/api/v1/game/" + str(game_id) +"/feed/live"
	game_content_json = cached_get_request(game_webpath)

	game_events = game_content_json["liveData"]["plays"]
	scoring_plays = game_events["scoringPlays"]
	all_plays = game_events["allPlays"]

	goal_event_list = [] # [{seconds_remaining, home_score, away_score},...]
	valid_periods = [1,2,3]
	for play in all_plays:
		if play["about"]["eventIdx"] in scoring_plays:

			period = play["about"]["period"]
			if period not in valid_periods:
				break

			extra_period_time = (3 - period) * 1200
			time_remaining_parsed = play["about"]["periodTimeRemaining"].split(":")
			seconds_remaining = int(time_remaining_parsed[0]) * 60 + int(time_remaining_parsed[1]) + extra_period_time
			home_score = play["about"]["goals"]["home"]
			away_score = play["about"]["goals"]["away"]

			goal_event_list.append({
									"seconds_remaining":seconds_remaining,
									"home_score":home_score, 
									"away_score":away_score
									})

	
	placed_bet = False
	bet_success = False
	is_failed_game = False
	failed_by_no_goal = False

	prev_time_remaining = 60 * 60
	prev_home_score = 0
	prev_away_score = 0
	prev_spread = 0

	for i, goal_event in enumerate(goal_event_list):

		current_time_remaining = goal_event["seconds_remaining"]
		current_home_score = goal_event["home_score"]
		current_away_score = goal_event["away_score"]
		current_spread = abs(current_home_score - current_away_score)

		# Skip the first goal
		if i != 0:

			if would_have_placed_bet(prev_spread, prev_time_remaining, current_time_remaining):
				count_bets += 1
				placed_bet = True

				if current_spread == prev_spread + 1:
					bet_success = True
					count_success += 1
				elif current_spread != prev_spread - 1:
					is_failed_game = True
					# print("\n\nERROR: failed on goal event: ")
					# print(json.dumps(goal_event, sort_keys=True))
					# print("Failed on game: ")
					# print(json.dumps(game_info, sort_keys=True))
				# else:
					# We lost the bet – do nothing :(
				break

		prev_time_remaining = current_time_remaining
		prev_home_score = current_home_score
		prev_away_score = current_away_score
		prev_spread = abs(prev_home_score - prev_away_score)

	# Inspect the last goal
	if not placed_bet and would_have_placed_bet(prev_spread, prev_time_remaining, 0):
		placed_bet = True
		count_bets += 1
		bet_success = False
		failed_by_no_goal = True

	# Output info about the game
	date = game_info["date"]
	home_team = game_content_json["gameData"]["teams"]["home"]["abbreviation"]
	away_team = game_content_json["gameData"]["teams"]["away"]["abbreviation"]
	home_score = game_info["home_score"]
	away_score = game_info["away_score"]
	
	bet_status = "No Bet"
	if is_failed_game:
		bet_status = "Analysis failed"
	elif placed_bet:
		if bet_success:
			bet_status = "Successful Bet"
		else:
			if failed_by_no_goal:
				bet_status = "Failed Bet - no goal"
			else:
				bet_status = "Failed Bet - opponent goal"

	print(date, away_team, away_score, " @ ", home_team, home_score, " - ", bet_status)

print("total", count_bets)
print("success", count_success)
print("failure", count_bets - count_success)
print("success rate: {:.4f}".format( (count_success*100) / count_bets))
