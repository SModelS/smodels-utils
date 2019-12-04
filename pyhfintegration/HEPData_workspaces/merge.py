import json

with open("sbottomA_900_250_60.json", 'r') as f1:
    j1 = json.load(f1)

with open("sbottomB_900_250_60.json", 'r') as f2:
    j2 = json.load(f2)
    
with open("sbottomC_900_250_60.json", 'r') as f3:
    j3 = json.load(f3)

jsonInputs = [j1, j2, j3]
# Concatenate (jsonInputs) -> jsonInput
jsonInput = {}
jsonInput["channels"] = []
for inpt in jsonInputs:
    for channel in inpt["channels"]:
        jsonInput["channels"].append(channel)
jsonInput["observations"] = []
for inpt in jsonInputs:
    for observation in inpt["observations"]:
        jsonInput["observations"].append(observation)
jsonInput["measurements"] = jsonInputs[0]["measurements"]
jsonInput["version"] = jsonInputs[0]["version"]

with open("sbottom_merged_900_250_60.json", "w") as output:
    json.dump(jsonInput, output, indent=4)
