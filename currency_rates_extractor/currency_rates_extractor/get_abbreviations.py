import sys,io,json

abbreviations = {}
odd_line = True
currency = ''
with io.open('abbreviations.txt','r') as f:
	for line in f:
		line = line.strip().lower()
		if odd_line:
			currency = line
			odd_line = False
		else:
			abbreviations[currency] = line 
			odd_line = True

with io.open('abbreviations.json','w') as fjson:
	try:
		fjson.write(json.dumps(abbreviations,indent=3))
	except Exception as e:
		print("Could not write in file with exception -{}-".format(e))