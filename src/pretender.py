
# PretenderFile
# Interpreter for dom5 newlords files
# Author: Rafael Stauffer rafael.stauffer@gmx.ch
# Version: 0.1

import csv

class PretenderFile():
	def __init__(self):
		self.fileName = ""
		self.rawData = ''
		self.nations = {}
		self.readNationsLookup('nations.csv')
		
	def readNationsLookup(self, fileName):
		# nation csv file has following line structure: nationID,nationName,nationTitle,era
		self.nations = {}
		with open(fileName, 'r') as csvFile:
			csvReader = csv.reader(csvFile, delimiter = ",")
			for row in csvReader:
				nationID = int(row[0].strip())
				self.nations[nationID] = (row[1].strip(), row[2].strip(), row[3].strip())
		
	def open(self, fileName):
		self.fileName = fileName
		self.rawData = ''
		with open(fileName, 'rb') as pretFile:
			self.rawData = pretFile.read()
		if len(self.rawData) < 10:
			return False
		return self.isDominionFile()
			
	def getNation(self):
		nationID = self.rawData[26]
		
		nationCode = nationID
		#print("{} {}, {}".format(self.nations[nationCode][2], self.nations[nationCode][0], self.nations[nationCode][1]))
		return self.nations[nationCode]
		
	def getEra(self):
		return self.getNation()[2]
		
	def getNationName(self):
		return self.getNation()[0]
		
	def getFilename(self):
		return self.fileName
		
	def getName(self):
		xorValue = 79 #b'\x4F'
		terminator = 79 #b'O' #b'\x78'
		startPos = 132
		pretNameStr = ''
		readPos = 0
		
		lastRead = b'\x00'
		while lastRead != terminator:
			lastRead = self.rawData[startPos + readPos]
			readPos = readPos + 1
		
		for b in bytes(self.rawData[startPos:startPos+readPos-1]):
			pretNameStr = pretNameStr + chr(b ^ xorValue)
		
		#print(pretNameStr)
		return pretNameStr
		
	def isDominionFile(self):
		#print(self.rawData[3:6])
		return self.rawData[3:6] == b'DOM'
		
if __name__ == '__main__':
	print("Please start main.py")
