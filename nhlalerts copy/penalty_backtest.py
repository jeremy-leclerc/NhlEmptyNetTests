import json
from backtrack_analysis import get_backtest_plays_data

TARGET_STREAK = 3
TIME_CUTOFF = 15 * 60
NHL_REG_SEASON_DATES = [	("2019-10-02", "2020-01-07"),  
							("2018-10-03", "2019-04-06"), 
							("2017-10-04", "2018-04-08"), 
							("2016-10-12", "2017-04-09"), 
							("2015-10-07", "2016-04-10"),
							("2014-10-08", "2015-04-11")]
NHL_REG_SEASON_DATES = NHL_REG_SEASON_DATES[:] #to decide which games to analyze


def is_near_end_of_game(game_time):
	return game_time < TIME_CUTOFF

def get_time_remaining(play):
	period = play["about"]["period"]
	if period not in [1,2,3]:
		return 0

	extra_period_time = (3 - period) * 1200
	time_remaining_parsed = play["about"]["periodTimeRemaining"].split(":")
	return int(time_remaining_parsed[0]) * 60 + int(time_remaining_parsed[1]) + extra_period_time

print("Seasons analyzing: ", NHL_REG_SEASON_DATES)

season_info = {}


total_bets = 0
total_sucesses = 0
for start_date, end_date in NHL_REG_SEASON_DATES:

	season_info[start_date] = {}

	count_bets = 0
	count_success = 0

	games = get_backtest_plays_data(start_date, end_date)

	for game in games:

		#track home and away penalty totals
		# home_team = 
		home_team_streak = 0	

		game_play = game["game_play"]["liveData"]["plays"]["allPlays"]

		home_team_id = game["home_team_id"]
		away_team_id = game["away_team_id"]

		time_of_last_penalty_block = "0"

		plays = [p for p in game_play if p["result"]["eventTypeId"] == "PENALTY" or p["result"]["eventTypeId"] == "GOAL"]

		placed_bet = False
		bet_decision = False
		bet_win = False
		lose_by_no_goal = False
		time_of_last_penalty = None
		will_bet_at_time_remaining = None

		for play in game_play:

			play_type = play["result"]["eventTypeId"]

			if play_type == "PENALTY":
				#if there is a penalty calculate streak and time when to bet

				# Pick up here: 
				# 	we need to think about how to deal with the end of a game with multiple penalties
				# 	
				# is_near_end_of_game(get_time_remaining(play))

				infracting_team = play["team"]["id"]

				if infracting_team == home_team_id:
					home_team_streak = max(1, home_team_streak + 1)
				else:
					home_team_streak = min(-1, home_team_streak - 1)

				if abs(home_team_streak) >= TARGET_STREAK and not is_near_end_of_game(get_time_remaining(play)):
					# TODO: account for major penalties?
					will_bet_at_time_remaining = get_time_remaining(play) - (2 * 60)
				else:
					will_bet_at_time_remaining = None

			if play_type == "GOAL":
				#if there is a goal, see if goal was a bet

				# We don't bet during the power play
				if will_bet_at_time_remaining is None or \
					get_time_remaining(play) > will_bet_at_time_remaining:
					continue

				if abs(home_team_streak) < TARGET_STREAK:
					raise "ERROR: home_team_streak was not in target range"

				goal_team = 'home' if play["team"]["id"] == home_team_id else 'away'
				streak_team = 'home' if home_team_streak > 0 else 'away'

				if goal_team == streak_team:
					bet_decision = True
					placed_bet = True
					bet_win = True
					count_success += 1
				else:
					bet_decision = True
					placed_bet = True
					bet_win = False

				count_bets += 1
				break

		# Case where not more goals are scored in the game after bet was made
		if will_bet_at_time_remaining is not None and not bet_decision:
			bet_decision = True
			bet_win = False
			lose_by_no_goal = True

		# Output info about the game
		date = game["date"]
		home_team = game["home_team_name"]
		away_team = game["away_team_name"]
		home_score = game["home_score"]
		away_score = game["away_score"]
		
		bet_status = "No Bet"
		if placed_bet:
			if bet_win:
				bet_status = "Successful Bet"
			else:
				if lose_by_no_goal:
					bet_status = "Failed Bet - no goal"
				else:
					bet_status = "Failed Bet - opponent goal"

		print("{:^20}{:^30}{:<6}@{:^30}{:<6}- {:<20}".format(
			date, away_team, away_score, home_team, home_score, bet_status))

	print("total", count_bets)
	print("success", count_success)
	print("failure", count_bets - count_success)
	print("success rate: {:.4f}".format( (count_success*100) / count_bets))

	total_bets += count_bets
	total_sucesses += count_success
	print("------------------------------------END OF {}-{} SEASON------\
---------------------------------".format(start_date, end_date))

	#save season info
	season_info[start_date]["year"] = start_date
	season_info[start_date]["total bets"] = count_bets
	season_info[start_date]["sucessful bets"] = count_success
	season_info[start_date]["failed bets"] = count_bets - count_success
	season_info[start_date]["sucess rate"] = ((count_success*100) / count_bets)
	season_info[start_date]["target streak"] = TARGET_STREAK
	season_info[start_date]["time cutoff"] = TIME_CUTOFF


print("")
print("TOTAL FOR ALL YEARS")
print("Tartget Streak: ", TARGET_STREAK)
print("Time Cutoff: ", TIME_CUTOFF)
print("total", total_bets)
print("success", total_sucesses)
print("failure", total_bets - total_sucesses)
print("success rate: {:.4f}".format( (total_sucesses*100) / total_bets))
print("")
for year in season_info:
	print("")
	print("Year: ", season_info[year]["year"])
	print("Target Streak: ", season_info[year]["target streak"])
	print("Time Cutoff: ", (int(season_info[year]["time cutoff"]) / 60)," mins left")
	print("Total bets: ", season_info[year]["total bets"])
	print("Sucessful bets: ", season_info[year]["sucessful bets"])
	print("Failed bets: ", season_info[year]["failed bets"])
	print("Sucess rate: {:.4f}".format(season_info[year]["sucess rate"]))

print("-------------" * 6)







			



