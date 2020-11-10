import time
from flask import Flask
from flask import jsonify
from flask_cors import CORS
import os
import sys
import glob
import pprint
import pandas as pd
from datetime import datetime

pp = pprint.PrettyPrinter()


app = Flask(__name__)
CORS(app)


fields = ["customer_number", "day_part", "first_seen_utc", "model_id", "tts"]
df = pd.read_csv('./data_aug27.csv', usecols=fields, encoding='utf-8')
df.rename(columns={"first_seen_utc": "date"}, inplace=True)

START_DATE_OBJ = datetime.fromtimestamp(df.date.iloc[0])
END_DATE_OBJ = datetime.fromtimestamp(df.date.iloc[-1])
MONTH = START_DATE_OBJ.month


df.date = pd.to_datetime(df["date"], unit='s', utc=True)

hour_mapping = {}
for i in range(0,25):
	part = ""
	val = 0
	if i < 11:
		part = " AM"
	else:
		part = " PM"
	if (i%12) == 0:
		val = 12
	else:
		val = (i%12)
	hour_mapping[i] = str(val) + part


@app.route('/')
def index():
    return "<h1> Hello! You have reached the api for Restaurant Viz! </h1>"

@app.route('/time')
def get_current_time():
	return {'time': time.time()}


@app.route('/getCustomerCount')
def get_customer_count():
	
	newDF = df

	result = {}
	
	
	for i in range(START_DATE_OBJ.day, END_DATE_OBJ.day+1):
		print (newDF.columns.values.tolist())
		if 'date' in newDF.columns.values.tolist():
			print ("If Date is a column setting it to Index")
			newDF["date"] = newDF["date"].astype('datetime64[ns]')
			newDF.set_index('date', inplace=True)
		
		startTime = "2020-{0:02d}-{1:02d} 00:00:00".format(MONTH, i)
		endTime = "2020-{0:02d}-{1:02d} 23:59:59".format(MONTH, i)

		tmp = newDF.loc[startTime:endTime]
		
		if 'date' not in newDF.columns.values.tolist():
			print ("If Date not in column for newDF resetting Index")
			newDF.reset_index(inplace=True)
				
		
		tmp.reset_index(inplace=True)
		
		tmp = tmp.groupby(tmp.date.map(lambda t: t.hour)).count()
		tmp.index.names = ["hour"]
		tmp = tmp[["customer_number"]]
		tmp["time"] = tmp.index
		
		res = (tmp.to_json(orient="index", date_format="iso"))
		res = tmp.to_dict("index")

		for k in res.keys():
			n = hour_mapping[res[k]["time"]]
			res[k]["time"] = n

		date_time_obj = datetime.strptime(startTime, '%Y-%m-%d %H:%M:%S')
		date = date_time_obj.date()
		result[str(date)] = res


	pp.pprint(result)

	return result


@app.route('/getAvgTTS')
def get_avg_tts_by_hour():
	
	newDF = df
	

	result = {}
	
	for i in range(START_DATE_OBJ.day, END_DATE_OBJ.day+1):
		print (newDF.columns.values.tolist())
		if 'date' in newDF.columns.values.tolist():
			print ("If Date is a column setting it to Index")
			newDF["date"] = newDF["date"].astype('datetime64[ns]')
			newDF.set_index('date', inplace=True)
		
		startTime = "2020-{0:02d}-{1:02d} 00:00:00".format(MONTH, i)
		endTime = "2020-{0:02d}-{1:02d} 23:59:59".format(MONTH, i)
		
		tempDF = newDF.loc[startTime:endTime]
		
		if 'date' not in newDF.columns.values.tolist():
			print ("If Date not in column for newDF resetting Index")
			newDF.reset_index(inplace=True)
		
		tempDF.reset_index(inplace=True)
		
		tempDF = tempDF.groupby(tempDF.date.map(lambda t: t.hour))["tts"].mean()
		tempDF = tempDF.to_frame()
		
		tempDF.reset_index(inplace=True)
		tempDF.rename(columns={'date':'time'}, inplace=True)


		t = tempDF.to_dict("index")

		for k in t.keys():
			n = hour_mapping[t[k]["time"]]
			t[k]["time"] = n

		date_time_obj = datetime.strptime(startTime, '%Y-%m-%d %H:%M:%S')
		date = date_time_obj.date()

		result[str(date)] = t

	return result

@app.route('/getAvgTTSByDayPart')
def get_avg_tts_by_daypart():

	newDF = df
	
	mapping = {1: "breakfast", 2: "lunch", 3: "afternoon", 4: "dinner", 5: "evening", 6: "late night"}

	result = {}
	
	for i in range(START_DATE_OBJ.day, END_DATE_OBJ.day+1):
		print (newDF.columns.values.tolist())
		if 'date' in newDF.columns.values.tolist():
			print ("If Date is a column setting it to Index")
			newDF["date"] = newDF["date"].astype('datetime64[ns]')
			newDF.set_index('date', inplace=True)
		
		startTime = "2020-{0:02d}-{1:02d} 00:00:00".format(MONTH, i)
		endTime = "2020-{0:02d}-{1:02d} 23:59:59".format(MONTH, i)
		
		tempDF = newDF.loc[startTime:endTime]
		
		print ("done slicing")

		if 'date' not in newDF.columns.values.tolist():
			print ("If Date not in column for newDF resetting Index")
			newDF.reset_index(inplace=True)
		
		tempDF.reset_index(inplace=True)
		
		tempDF = tempDF.groupby(tempDF.day_part)["tts"].mean()
		
		tempDF = tempDF.to_frame()
		tempDF.reset_index(inplace=True)

		t = tempDF.to_dict("index")

		for k in t.keys():
			n = mapping[t[k]["day_part"]]
			t[k]["name"] = n

		date_time_obj = datetime.strptime(startTime, '%Y-%m-%d %H:%M:%S')
		date = date_time_obj.date()

		result[str(date)] = t

	return result

@app.route('/getTTSDistribution')
def get_dist_tts():


	newDF = df

	result = {}
	weeks = [g.reset_index() for n, g in df.groupby(pd.Grouper(key='date',freq='W'))]

	for j in range(len(weeks)):
		a = weeks[j].tts.value_counts()
		a = a.to_frame()
		a.reset_index(inplace=True)
		a.rename(columns={"index": "tts", "tts": "count"}, inplace=True)
		z = a.to_dict("index")
		for i in range(len(z)):
			z[i]["name"]= z[i]["tts"]
		result[j] = z
	return result

port = int(os.environ.get('PORT', 5000))
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=port)
