
import datetime
import json
import subprocess


def shouldRefresh(recurrence, todayDate, lastUpdatedDate):
	if recurrence['type'] == 'daily':
		return todayDate != lastUpdatedDate
	elif recurrence['type'] == 'weekly':
		if todayDate == lastUpdatedDate:
			return False
		tempDate = todayDate - datetime.timedelta(1)
		while lastUpdatedDate < tempDate:
			if tempDate == lastUpdatedDate:
				return False
			elif tempDate.weekday() == recurrence['day']:
				return True
			tempDate = tempDate - datetime.timedelta(1)
	elif recurrence['type'] == 'monthly':
		lastResetDate = todayDate.replace(day=1)
		if todayDate == lastUpdatedDate:
			return False
		return lastResetDate > lastUpdatedDate
	return False


def stringToDate(string):
	return datetime.datetime.strptime(string, "%Y-%m-%d").date()


def dumpJSON(filePath, data):
	with open(filePath, 'w') as outfile:
		json.dump(data, outfile, indent=4)


def registerTasks(jsonData, todayDate, lastUpdatedDate):
	recursiveRegister(jsonData, "", todayDate, lastUpdatedDate)


def recursiveRegister(jsonData, categoryString, todayDate, lastUpdatedDate):
	if not jsonData:
		return
	for k, v in jsonData.items():
		if k not in ["tasks", "recurrence", "lastdate"]:
			recursiveRegister(v, categoryString + "." + k, todayDate, lastUpdatedDate)
	if "tasks" in jsonData and type(jsonData["tasks"]) == list and "recurrence" in jsonData and shouldRefresh(jsonData["recurrence"], todayDate, lastUpdatedDate):
		command = "todo rmctx " + categoryString + " --force"
		print(command)
		subprocess.call(command)
		for task in jsonData["tasks"]:
			command = "todo add \"" + task + "\" --context " + categoryString
			print(command)
			subprocess.call(command)  # TODO pool these calls


configPath = "config.json"
with open(configPath) as data_file:
	data = json.load(data_file)

todayDate = datetime.datetime.utcnow().date()
lastUpdatedDate = stringToDate(data["lastdate"]) if "lastdate" in data else (todayDate - datetime.timedelta(999))

registerTasks(data, todayDate, lastUpdatedDate)  # TODO save and load last updated time

data["lastdate"] = str(todayDate)

dumpJSON(configPath, data)
