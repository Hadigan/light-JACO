import pickle
import os
import math

def parse_spe_txt_to_pikle(spe_txt_file, spe_path:str):
    print(f"parse spe {spe_txt_file} to pikle {spe_path}")
    results = []
    f = open(spe_txt_file, "r")
    for index, line in enumerate(f.readlines()):
        if not line.startswith("[BR]"):
            continue
        parsed_line = line.split("/")
        pc = int(parsed_line[1], 16)
        inst = parsed_line[2]
        event = parsed_line[3]
        target = int(parsed_line[4], 16)
        results.append((pc, inst, event, target))
    print(f"number of records of spe {spe_txt_file} is {len(results)}")
    
    chunk_count = 128
    chunk_size = math.ceil(len(results) / chunk_count)
    print(f"chunk len: {chunk_count*chunk_size}")


    for i in range(chunk_count):
        chunk = results[i * chunk_size : (i+1) * chunk_size]
        chunk_pkl_filename = os.path.join(spe_path, f"{i}.pkl")
        pickle.dump(chunk, open(chunk_pkl_filename, "wb"))



if __name__ == "__main__":
    spe_file = "/home/linwh/workspaces/light-jaco/spe/carts2-spe.txt"
    spe_path = "/home/linwh/workspaces/light-jaco/spe/carts2-spes2"
    if not os.path.exists(spe_path):
        os.mkdir(spe_path)
    parse_spe_txt_to_pikle(spe_file, spe_path)