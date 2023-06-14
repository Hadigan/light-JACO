import pickle
import math
import os

spe_path = "/home/linwh/workspaces/light-jaco/spe/carts2-spes"
pkl_file = "/home/linwh/workspaces/light-jaco/spe/carts2-spe.pkl"
parsed_data = pickle.load(open(pkl_file, 'rb'))
print(f"total len: {len(parsed_data)}")
chunk_count = 128
chunk_size = math.ceil(len(parsed_data) / chunk_count)
print(f"chunk len: {chunk_count*chunk_size}")


for i in range(chunk_count):
    chunk = parsed_data[i * chunk_size : (i+1) * chunk_size]
    chunk_pkl_filename = os.path.join(spe_path, f"{i}.pkl")
    pickle.dump(chunk, open(chunk_pkl_filename, "wb"))

