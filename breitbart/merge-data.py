import json
import glob
import tqdm

read_files = glob.glob("data/*.txt")
output_list = []

for f in read_files:
    with open(f, "r") as infile:
        output_list.append(json.load(infile))

output_list = [item for sublist in tqdm.tqdm(output_list,desc='Flattening') for item in sublist]

with open("breitbart_data.json", "w") as outfile:
    json.dump(output_list, outfile)

with open("breitbart_datap.json", "w") as outfile:
    json.dump(output_list, outfile, indent=4, sort_keys=True)
