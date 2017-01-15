import xmind
import datetime
import json


def shouldRefresh(recurrence, lastUpdatedDate, todayDate):
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


def writeConfigFromXMind(subtopics, config):
	for subtopic in subtopics:
		config.add_section(subtopic.getTitle())
		tasklist = []
		for subsubtopic in subtopic.getSubTopics():
			tasklist.append(subsubtopic.getTitle())
		config.set(subtopic.getTitle(), 'tasks', str(tasklist))


def saveConfig(config):
	with open(configPath, 'w') as configfile:
		config.write(configfile)


configPath = "config.json"
with open(configPath) as data_file:
	data = json.load(data_file)
filepath = data["metadata"]["filename"]
sheetname = data["metadata"]["sheetname"]
workbook = xmind.load(filepath)

sheets = workbook.getSheets()
matchingsheets = [sheet for sheet in sheets if sheet.getTitle() == sheetname]
if len(matchingsheets) > 1:
	raise ValueError('Was expecting only one sheet named %s in %s, got %d' % (
		sheetname, filepath, len(matchingsheets)))
elif len(matchingsheets) == 0:
	sheet = workbook.getPrimarySheet()
	sheet.setTitle(sheetname)
else:
	sheet = matchingsheets[0]

rootTopic = sheet.getRootTopic()

rootContentKeys = data["contents"].keys()
if len(rootContentKeys) > 1:
	raise ValueError('Was expecting only one root topic in contents in %s, got %d' % (
		configPath, len(rootContentKeys)))
elif len(rootContentKeys) == 0:
	raise ValueError('Was expecting a root topic in contents in %s' % (
		configPath,))


rootContentKey = rootContentKeys[0]
rootTopic.setTitle(rootContentKey)

subTopics = rootTopic.getSubTopics()
if not subTopics:
	subTopics = []
subTopicTitles = list(subTopic.getTitle().encode("utf-8") for subTopic in subTopics)

configTopicKeys = data["contents"][rootContentKey]["topics"].keys()
todayDate = datetime.datetime.utcnow().date()
rootTopicNotes = rootTopic.getNotes()
if rootTopicNotes:
	rootTopicNotesText = rootTopicNotes.getContent().encode("utf-8")
	lastUpdatedDate = stringToDate(rootTopicNotesText)
else:
	lastUpdatedDate = datetime.date.min
rootTopic.setPlainNotes(str(todayDate))

for configTopicKey in configTopicKeys:
	configTopic = data["contents"][rootContentKey]["topics"][configTopicKey]
	recurrence = configTopic["recurrence"]
	if shouldRefresh(recurrence, lastUpdatedDate, todayDate):
		# add subtopic from config if it is not in the sheet
		if configTopicKey not in subTopicTitles:
			subTopic = xmind.core.topic.TopicElement()
			subTopic.setTitle(configTopicKey)
			rootTopic.addSubTopic(subTopic)
		else:
			# if it is in the sheet, get it
			subTopic = next(subTopic for subTopic in subTopics if subTopic.getTitle() == configTopicKey)
		tasks = configTopic["tasks"]
		# get existing task topics
		existingTaskTopics = subTopic.getSubTopics()
		if not existingTaskTopics:
			existingTaskTopics = []
		existingTaskTopicTitles = list(existingTaskTopic.getTitle().encode("utf-8") for existingTaskTopic in existingTaskTopics)
		for task in tasks:
			if task not in existingTaskTopicTitles:
				newTaskTopic = xmind.core.topic.TopicElement()
				newTaskTopic.setTitle(task)
				subTopic.addSubTopic(newTaskTopic)

xmind.save(workbook, filepath)
