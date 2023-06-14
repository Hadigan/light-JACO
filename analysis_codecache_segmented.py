
import math
import pickle
import sys
from typing import List,Dict
import math
import csv
import os
import re

DISTANCE_128M = 128*1024*1024
DISTANCE_1M = 1*1024*1024


class CodeBlob():
    def __init__(self, name) -> None:
        self.name:str = name
        self.start_address = 0
        self.end_address = 0
        self.maincode_start_address = None
        self.maincode_end_address = None
        self.stubcode_start_address = None
        self.stubcode_end_address = None
        self.compile_level = -1
        self.is_from_map = False
        self.is_nmethod = False
    
    def copy_from(self, source):
        self.name = source.name
        self.start_address = source.start_address
        self.end_address = source.end_address
        self.maincode_start_address = source.maincode_start_address
        self.maincode_end_address = source.maincode_end_address
        self.stubcode_start_address = source.stubcode_start_address
        self.stubcode_end_address = source.stubcode_end_address
        self.compile_level = source.compile_level
        self.is_from_map = source.is_from_map
        self.is_nmethod = source.is_nmethod
    
    def change_address_by_offset(self, offset, split_maincode):
        if self.maincode_start_address:
            self.maincode_start_address += offset
        if self.maincode_end_address:
            self.maincode_end_address += offset
        if self.stubcode_start_address:
            self.stubcode_start_address += offset
        if self.stubcode_end_address:
            self.stubcode_end_address += offset
        if split_maincode:
            self.start_address = self.maincode_start_address
            self.end_address = self.stubcode_end_address
        else:
            self.start_address += offset
            self.end_address += offset
    
    def set_maincode_address(self, start, end):
        self.maincode_start_address = start
        self.maincode_end_address = end
        
    def set_codeblob_address(self, start, end):
        self.start_address = start
        self.end_address = end
    
    def set_stubcode_address(self, start, end):
        self.stubcode_start_address = start
        self.stubcode_end_address = end
    
    def set_compile_level(self, level):
        self.compile_level = level
    
    def is_vtable(self):
        return self.name.startswith("vtable") or self.name.startswith("itable")
    
    def get_size(self):
        return self.end_address - self.start_address

    def set_is_from_map(self, is_from_map):
        self.is_from_map = is_from_map
        return
    
    def set_is_nmethod(self, is_nmethod):
        self.is_nmethod = is_nmethod
        return

    def code_start_address(self):
        if self.is_nmethod and self.maincode_start_address and self.maincode_end_address and self.stubcode_start_address and self.stubcode_end_address:
            return self.maincode_start_address
        else:
            return self.start_address
    
    def code_end_address(self):
        if self.is_nmethod and self.maincode_start_address and self.maincode_end_address and self.stubcode_start_address and self.stubcode_end_address:
            return self.stubcode_end_address
        else:
            return self.end_address
    
    def get_code_size(self):
        if self.is_nmethod and self.maincode_start_address and self.maincode_end_address and self.stubcode_start_address and self.stubcode_end_address:
            return self.stubcode_end_address - self.maincode_start_address
        else:
            return self.get_size()
    
    def print(self):
        print(f"Method name:{self.name}")
        print("Address:[{},{}]".format(hex(self.start_address), hex(self.end_address)))
    
    def in_maincode(self, address):
        return address >= self.maincode_start_address and address < self.maincode_end_address
    
    def in_stubcode(self, address):
        if self.stubcode_end_address - self.stubcode_start_address > 4:
            return address >= self.stubcode_start_address and address < self.stubcode_end_address
        else:
            return False

def check_method_order(methods:List[CodeBlob]):
    method_len = len(methods)
    for i in range(method_len-1):
        if methods[i].start_address >= methods[i+1].start:
            return False
    return True

def binary_search(methods:List[CodeBlob], pc):
    l = 0
    r = len(methods) - 1
    while l <= r:
        m = (l + r) // 2
        if methods[m].start_address <= pc and pc < methods[m].end_address:
            return methods[m]
        elif pc < methods[m].start_address:
            r = m - 1
        else:
            l = m + 1
    return None

def search_by_name(methods:List[CodeBlob], name):
    for method in methods:
        if method.name == name:
            return method
    return None

def type_distribution(parsed_data):
    result = {}
    total = len(parsed_data)
    for t in parsed_data:
        inst = t[1]
        if inst not in result:
            result[inst] = 0
        result[inst] += 1
    result = {inst:result[inst]/total for inst in result}
    print("type_distribution")
    print("total: {}".format(total))
    print(result)
    print("---------------------------------------------")
    
def distance_distribution(parsed_data):
    result = {"B>128M":0, "BIND>128M":0, "BCOND>128M":0, "other":0}
    total = len(parsed_data)
    for t in parsed_data:
        pc = t[0]
        inst = t[1]
        target = t[2]
        distance = abs(target-pc)
        if distance > DISTANCE_128M:
            if inst == "B":
                result["B>128M"] += 1
            elif inst == "B IND":
                result["BIND>128M"] += 1
            elif inst == "B COND":
                result["BCOND>128M"] += 1
            else:
                result["other"] += 1
    
    result = {inst:result[inst]/total for inst in result}
    print("distance_distribution")
    print(result)
    print("---------------------------------------------")

def branch_miss_counter(parsed_data):
    total_branch_loads = len(parsed_data)
    total_branch_misses = 0
    for t in parsed_data:
        miss = t[3]
        if miss:
            total_branch_misses += 1
    print("branch_miss_counter")
    print("total branch loads: {}".format(total_branch_loads))
    print("total branch misses: {}".format(total_branch_misses))
    print("branch miss rate: {}".format(total_branch_misses/total_branch_loads))
    print("---------------------------------------------")

def branch_miss_distribution(parsed_data):
    result_type = {}
    result_distance = {">128M": 0, "<128M":0}
    total_branch = len(parsed_data)
    total_miss = 0
    for t in parsed_data:
        pc = t[0]
        inst = t[1]
        target = t[2]
        miss = t[3]
        distance = abs(target-pc)
        if miss:
            total_miss += 1
            if distance > DISTANCE_128M:
                result_distance[">128M"] += 1
            else:
                result_distance["<128M"] += 1
            if inst not in result_type:
                result_type[inst] = 0
            result_type[inst] += 1
    result_type = {inst:result_type[inst]/total_branch for inst in result_type}
    result_distance = {inst:result_distance[inst]/total_branch for inst in result_distance}
    print("branch_miss_distribution")
    print(result_type)
    print(result_distance)
    print("---------------------------------------------")

def B_distance_distribution(parsed_data):
    all_distance_distribution = [0 for i in range(128)]
    miss_distance_distribution = [0 for i in range(128)]
    for t in parsed_data:
        pc = t[0]
        inst = t[1]
        target = t[2]
        miss = t[3]
        distance = abs(target-pc)
        if inst == "B":
            # log_distance = math.floor(math.log2(distance))
            log_distance = math.floor(distance / DISTANCE_1M)
            all_distance_distribution[log_distance] += 1
            if miss:
                miss_distance_distribution[log_distance] += 1
    
    print("B_distance_distribution")
    print(all_distance_distribution)
    print(miss_distance_distribution)
    total_b = sum(all_distance_distribution)
    total_b_miss = sum(miss_distance_distribution) + 0.000000000001
    all_distance_distribution = [i/total_b for i in all_distance_distribution]
    miss_distance_distribution = [i/total_b_miss for i in miss_distance_distribution]
    print(all_distance_distribution)
    print(miss_distance_distribution)
    print("---------------------------------------------")
    
    csv_writer = csv.writer(open('distance.csv', "wt"))
    
    csv_writer.writerow(['distance', 'all-percent', 'miss-percent'])

    for i in range(128):
        csv_writer.writerow([i, all_distance_distribution[i], miss_distance_distribution[i]])

def resort_methods(methods):
    methods.sort(key= lambda x: x.start_address, reverse=False)


# Method Name:VtableBlob: vtable chunks
# Address Range:[0x0000ffff9753ba10,0x0000ffff9753bab8]

# Method Name:org.apache.cassandra.utils.btree.BTree.applyLeaf([Ljava/lang/Object;Ljava/util/function/BiConsumer;Ljava/lang/Object;)V
# Address Range:[0x0000ffff9753bd10,0x0000ffff9753c448]
# main code:[0x0000ffff9753bf00,0x0000ffff9753c140]
# stub code:[0x0000ffff9753c140,0x0000ffff9753c200]
# CompLevel:4
# HotnessCounter:640

def parse_a_codecache_record(lines: List[str]) -> CodeBlob:
    assert len(lines) >= 2
    assert(lines[0].startswith("Method Name:"))
    assert(lines[1].startswith("Address Range:"))
    
    name = lines[0].strip().split(":")[1]
    codeblob_address = lines[1].strip().split(":")[1].replace("[", "").replace("]", "").split(",")
    is_nmethod = False
    if len(lines) == 6:
        is_nmethod = True
    new_codeblob = CodeBlob(name)
    new_codeblob.set_codeblob_address(int(codeblob_address[0], 16), int(codeblob_address[1], 16))
    new_codeblob.set_maincode_address(int(codeblob_address[0], 16), int(codeblob_address[1], 16))
    new_codeblob.set_stubcode_address(int(codeblob_address[1], 16), int(codeblob_address[1], 16))
    new_codeblob.set_is_nmethod(is_nmethod)
    if is_nmethod:
        assert(lines[2].startswith("main code:"))
        assert(lines[3].startswith("stub code:"))
        assert(lines[4].startswith("CompLevel:"))
        
        maincode_address = lines[2].strip().split(":")[1].replace("[", "").replace("]", "").split(",")
        stubcode_address = lines[3].strip().split(":")[1].replace("[", "").replace("]", "").split(",")
        compile_level = int(lines[4].strip().split(":")[1])
        
        new_codeblob.set_maincode_address(int(maincode_address[0], 16), int(maincode_address[1], 16))
        new_codeblob.set_stubcode_address(int(stubcode_address[0], 16), int(stubcode_address[1], 16))
        new_codeblob.set_compile_level(compile_level)
        new_codeblob.set_is_from_map(False)
    return new_codeblob

def parse_codecache(codecache_filename):
    codecache = open(codecache_filename, "r")
    lines = codecache.readlines()
    a_record_lines:List = []
    methods:List[CodeBlob] = []
    
    for line in lines:
        if line.startswith("Method Name:"):
            a_record_lines = []
        if line == "\n":
            methods.append(parse_a_codecache_record(a_record_lines))
        elif line.startswith("HotnessCounter:"):
            a_record_lines.append(line)
            methods.append(parse_a_codecache_record(a_record_lines))
        a_record_lines.append(line)
    
    methods.sort(key= lambda x: x.start_address, reverse=False)
    
    return methods

def parse_map(map_filename):
    lines = open(map_filename, "r").readlines()
    methods:List[CodeBlob]  = []
    same_name_index = {}
    pattern = re.compile("([0-9a-f]+) ([0-9a-f]+) (.+)\n")
    for line in lines:
        match = pattern.match(line)
        if not match:
            continue
        
        start_address = int(match.group(1), 16)
        size = int(match.group(2), 16)
        name = match.group(3)

        end_address = start_address+size
        new_method = CodeBlob(name)
        new_method.set_codeblob_address(start_address, end_address)
        new_method.set_compile_level(5)
        new_method.set_is_from_map(True)
        new_method.set_is_nmethod(False)
        methods.append(new_method)
    methods.sort(key= lambda x: x.start_address, reverse=False)
    return methods

def parse_map_file(map_filename):
    lines = open(map_filename, "r").readlines()
    methods:List[CodeBlob]  = []
    same_name_index = {}
    pattern = re.compile("([0-9a-f]+) ([0-9a-f]+) (.+)\n")
    for line in lines:
        match = pattern.match(line)
        if not match:
            continue
        
        start_address = int(match.group(1), 16)
        size = int(match.group(2), 16)
        name = match.group(3)
        if name in same_name_index:
            same_name_index[name] += 1
            name = name + str(same_name_index[name])
        else:
            same_name_index[name] = 1
        end_address = start_address+size
        new_method = CodeBlob(name)
        new_method.set_codeblob_address(start_address, end_address)
        new_method.set_compile_level(5)
        new_method.set_is_from_map(True)
        new_method.set_is_nmethod(False)
        methods.append(new_method)
    
    return methods

# [8.947s][trace][vtablestubs] vtable 107 0x00007f0a54be49b0 0x00007f0a54be49de
def parse_vtable_file(vtable_filename):
    lines = open(vtable_filename, "r").readlines()
    vtables:List[CodeBlob] = []
    pattern = re.compile(".+\[trace\]\[vtablestubs\] ([vi]table) ([0-9]+) (0x[0-9a-f]+) (0x[0-9a-f]+)")
    for line in lines:
        match = pattern.match(line)
        if not match:
            continue
        
        start_address = int(match.group(3), 16)
        end_address   = int(match.group(4), 16)
        size = end_address - start_address
        name = "{}-{}".format(match.group(1), match.group(2))
        new_nmethod = CodeBlob(name)
        new_nmethod.set_codeblob_address(start_address, end_address)
        new_nmethod.set_compile_level(5)
        new_nmethod.set_is_from_map(True)
        new_nmethod.set_is_nmethod(False)
        
        vtables.append(new_nmethod)
    
    return vtables 

def parse_nmethod_address(codecache_filename, map_filename, vtable_filename):
    method_from_codecache:List[CodeBlob] = parse_codecache(codecache_filename)
    methods_from_map:List[CodeBlob] = parse_map_file(map_filename)
    methods:List[CodeBlob] = []
    methods_has_added = set()
    
    for method in method_from_codecache:
        methods.append(method)
        methods_has_added.add(method.name)
    for method in methods_from_map:
        if method.name not in methods_has_added:
            methods.append(method)
            methods_has_added.add(method.name)
    
    if vtable_filename:
        vtables:List[CodeBlob] = parse_vtable_file(vtable_filename)
        for method in methods:
            if method.name.startswith("vtable") or method.name.startswith("itable"):
                methods.remove(method)
        for vtable in vtables:
            methods.append(vtable)
    
    methods.sort(key= lambda x: x.start_address, reverse=False)
    
    return methods
    
        
def B_miss_from(parsed_data,codecache_filename, map_filename):
    methods:List[CodeBlob] = parse_nmethod_address(codecache_filename, map_filename)
    
    # 先看B BL 和 BIND 分支的来源分布。扣除掉BCOND，
    
    result_miss = {}
    result_all = {}
    # 再看 B BIND 分支miss的来源分布，扣除掉BCOND
    total_branch = len(parsed_data)
    total_BL = 0
    total_BIND = 0
    for t in parsed_data:
        pc = t[0]
        inst = t[1]
        target = t[2]
        miss = t[3]
        distance = abs(target-pc)
        if inst == "B":
            total_BL += 1
        if inst == "B IND":
            total_BIND += 1
        if inst != "B COND":
            source_method = binary_search(methods, pc)
            pc_offset = ""
            if source_method != None:
                source_name = source_method.name
                pc_offset = hex(pc - source_method.start_address)
            else:
                source_name = "nomethod"
            target_method = binary_search(methods, target)
            if target_method != None:
                target_name = target_method.name
            else:
                target_name = "nomethod"
            hash_str = "[{}]{}({})->{}".format(inst, source_name, pc_offset, target_name)
            
            if hash_str not in result_all:
                result_all[hash_str] = 0
            result_all[hash_str] += 1
            if miss:
                if hash_str not in result_miss:
                    result_miss[hash_str] = 0
                result_miss[hash_str] += 1
            
    result_miss = sorted(result_miss.items(), key= lambda x: x[1], reverse=False)
    result_all  = sorted(result_all.items(), key= lambda x : x[1], reverse=False)
    # for r in result_miss:
    #     print("{}: {}".format(r[0], r[1]))
    
    
def vtable_contribution(parsed_data,codecache_filename, map_filename):
    methods:List[CodeBlob] = parse_nmethod_address(codecache_filename, map_filename)
    
    total_branch = len(parsed_data)
    total_vtable = 0
    total_miss = 0
    total_bl_miss = 0
    total_bind_miss = 0
    total_bl = 0
    total_bind = 0
    total_BL_vtable = 0
    total_BIND_vtable = 0
    total_BL_vtable_miss = 0
    total_BIND_vtable_miss = 0
    total_BCOND = 0
    total_BCOND_miss = 0
    for t in parsed_data:
        pc = t[0]
        inst = t[1]
        target = t[2]
        miss = t[3]
        distance = abs(target-pc)
        if miss:
            total_miss += 1
            if inst == "B":
                total_bl_miss += 1
            if inst == "B IND":
                total_bind_miss += 1
            if inst == "B COND":
                total_BCOND_miss += 1
        if inst == "B":
            total_bl += 1
        if inst == "B IND":
            total_bind += 1
        if inst == "B COND":
            total_BCOND += 1
        
        if inst == "B COND":
            continue
        
        source_method = binary_search(methods, pc)
        target_method = binary_search(methods, target)
        if target_method == None:
            continue
        if not target_method.is_vtable():
            continue
        
        total_vtable += 1
        if inst == "B":
            total_BL_vtable += 1
            if miss:
                total_BL_vtable_miss += 1
        if inst == "B IND":
            total_BIND_vtable += 1
            if miss:
                total_BIND_vtable_miss += 1
                
    print("target->vtable prob: {}".format(total_vtable / total_branch))
    print("vtable miss ratio: {}".format((total_BL_vtable_miss + total_BIND_vtable_miss) / total_branch))
    print("vtable miss rate: {}".format((total_BL_vtable_miss + total_BIND_vtable_miss) / total_vtable))
    print("total miss rate: {}".format(total_miss / total_branch))
    
    
    print("vtable from BL: {}".format(total_BL_vtable / total_vtable))
    print("vtable from BIND: {}".format(total_BIND_vtable / total_vtable))
    print("vtable miss from BL: {}".format(total_BL_vtable_miss / (0.0000000000001 + total_BL_vtable_miss + total_BIND_vtable_miss)))
    print("vtable miss from BIND: {}".format(total_BIND_vtable_miss / (0.00000000000001 + total_BL_vtable_miss + total_BIND_vtable_miss)))
    
    
    print("total bl miss rate: {}".format(total_bl_miss / total_bl))
    print("total bind miss rate: {}".format(total_bind_miss / total_bind))
    
    print("normal bl miss rate: {}".format((total_bl_miss - total_BL_vtable_miss) / total_bl))
    print("normal bind miss rate: {}".format((total_bind_miss - total_BIND_vtable_miss) / total_bind))
    print("normal bcond miss rate: {}".format(total_BCOND_miss/total_BCOND))
    
    print("vtable bl miss rate: {}".format(total_BL_vtable_miss / total_BL_vtable))
    print("vtable bind miss rate: {}".format(total_BIND_vtable_miss / (0.00000000000001 + total_BIND_vtable)))
    
    
    
    
            
            
    
        
        

if __name__ == "__main__":
    data_path = sys.argv[1]
    parsed_spe_data_filename = os.path.join(data_path, "parsed-spe.pkl")
    assert(os.path.exists(parsed_spe_data_filename))
    codecache_filename = os.path.join(data_path, "codecache")
    assert(os.path.exists(codecache_filename))
    map_filename = os.path.join(data_path, "codecache.map")
    assert(os.path.exists(map_filename))
    # (pc, inst, target)
    parsed_data:List[tuple] = pickle.load(open(parsed_spe_data_filename, 'rb'))
    type_distribution(parsed_data)
    # distance_distribution(parsed_data)
    # branch_miss_counter(parsed_data)
    # branch_miss_distribution(parsed_data)
    # B_distance_distribution(parsed_data)
    # B_miss_from(parsed_data, codecache_filename, map_filename)
    vtable_contribution(parsed_data, codecache_filename, map_filename)