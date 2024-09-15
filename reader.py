# IDK if you need this in the repo, just takes files from @RoboFun01 and gives list for main OSM data :)
import json

with open("C:/Users/LENOVO/Downloads/aerodrome_get_step2.json") as f:
	data = json.load(f)

values = [block["PARAMETERS"]["VALUE"][1:][:-1] for block in data]
print(values)
