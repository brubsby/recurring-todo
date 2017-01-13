import ConfigParser
import xmind
import pprint
import ast
import datetime


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
	with open(configpath, 'w') as configfile:
		config.write(configfile)


configpath = "config.ini"
config = ConfigParser.SafeConfigParser()
config.read(configpath)
filepath = "runescape.xmind"
sheetname = "runescape"
workbook = xmind.load(filepath)

sheets = workbook.getSheets()
matchingsheets = [sheet for sheet in sheets if sheet.getTitle() == sheetname]
if len(matchingsheets) != 1:
	raise ValueError('Was expecting only one sheet named %s in %s, got %d' % (
		sheetname, filepath, len(matchingsheets)))

sheet = matchingsheets[0]
rootTopic = sheet.getRootTopic()
subTopics = rootTopic.getSubTopics()
if not subTopics:
	subTopics = []
subTopicTitles = list(subTopic.getTitle().encode("utf-8") for subTopic in subTopics)

configSections = config.sections()
todayDate = datetime.datetime.utcnow().date()
rootTopicNotes = rootTopic.getNotes()
if rootTopicNotes:
	rootTopicNotesText = rootTopicNotes.getContent().encode("utf-8")
	lastUpdatedDate = stringToDate(rootTopicNotesText)
else:
	lastUpdatedDate = datetime.date.min
rootTopic.setPlainNotes(str(todayDate))

for configSection in configSections:
	recurrence = ast.literal_eval(config.get(configSection, "recurrence"))
	if shouldRefresh(recurrence, lastUpdatedDate, todayDate):
		# add subtopic from config if it is not in the sheet
		if configSection not in subTopicTitles:
			subTopic = xmind.core.topic.TopicElement()
			subTopic.setTitle(configSection)
			rootTopic.addSubTopic(subTopic)
		else:
			# if it is in the sheet, get it
			subTopic = next(subTopic for subTopic in subTopics if subTopic.getTitle() == configSection)
		tasks = ast.literal_eval(config.get(configSection, "tasks"))
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
