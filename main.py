from multiprocessing import Pool, current_process
import math
import analysis_codecache_segmented
from typing import List,Dict
import pickle
from pathlib import Path
from statis_class import IndirectBranchMiss,IndirectMethon2Runtime,MethodCall
number_of_pool = 128
number_of_chunk = 128

def branch_type_reduce(spe_pikle_file, map_file):
    # 对输入的元素块进行处理，每个块包含多个元素
    # 返回结果是每个进程处理的元素块的统计结果
    parsed_data:List[tuple] = pickle.load(open(spe_pikle_file, 'rb'))
    methods:List[analysis_codecache_segmented.CodeBlob] = analysis_codecache_segmented.parse_codecache(map_file)   
    start_address = methods[0].start_address - 100*1024*1024
    end_address = methods[-1].end_address + 100*1024*1024
    length_count_dict = {"B COND":0, "B":0, "B IND":0, "BL":0}
    lens = 0
    for element in parsed_data:
        pc = element[0]
        inst = element[1]
        event:str = element[2]
        target = element[3]

        if pc < start_address or pc > end_address:
            continue
        if target < start_address or target > end_address:
            continue

        caller_method = analysis_codecache_segmented.binary_search(methods, pc)
        callee_method = analysis_codecache_segmented.binary_search(methods, target)
        
        if caller_method == None or callee_method == None:
            continue
        # if caller_method.name == callee_method.name:
        #     continue
        if event.find("MISPRED") == -1:
            continue
        if inst == "B COND":
            length_count_dict["B COND"] += 1
        elif inst == "B":
            if caller_method.name == callee_method.name:
                if caller_method.in_maincode(pc) and callee_method.in_maincode(target):
                    length_count_dict["B"] += 1
                else:
                    length_count_dict["BL"] += 1
            else:
                length_count_dict["BL"] += 1
        elif inst == "B IND":
            length_count_dict["B IND"] += 1
        else:
            print("else")

    return length_count_dict

def branch_type_map(results):
    # 更新全局结果
    result = {"B COND":0, "B":0, "B IND":0, "BL":0}
    for r in results:
        for b in r:
            result[b] += r[b]
    total = 0
    print(result)
    for b in result:
        total += result[b]
    result = [result[b]/total for b in result]
    # 打印结果
    print(result)

def statis_method_call(pc,inst,target,caller:analysis_codecache_segmented.CodeBlob,callee:analysis_codecache_segmented.CodeBlob,methodcall_result:MethodCall):
    if caller.compile_level == 5:
        return
    if inst == "B":
        if caller.name == callee.name and callee.in_stubcode(target):
            methodcall_result.BL2stub += 1
        elif caller.name != callee.name and caller.in_maincode(pc) and callee.in_maincode(target):
            methodcall_result.BL2method += 1
        elif caller.compile_level != 5 and callee.compile_level == 5:
            if callee.name.startswith("vtable"):
                methodcall_result.BL2vtable += 1
            elif  callee.name.startswith("StubRoutines"):
                methodcall_result.BL2stubroutine += 1
            else:
                methodcall_result.BL2runtime += 1
    elif inst == "B IND":
        if caller.compile_level != 5 and caller.in_stubcode(pc):
            if callee.compile_level == 5:
                if callee.name.startswith("vtable"):
                    methodcall_result.stub2vtable += 1
                elif  callee.name.startswith("StubRoutines"):
                    methodcall_result.stub2stubroutine += 1
                else:
                    methodcall_result.stub2runtime += 1
            elif callee.compile_level != 5 and callee.in_maincode(target):
                methodcall_result.stub2method += 1
        elif caller.compile_level != 5 and caller.in_maincode(pc) and callee.compile_level == 5:
            methodcall_result.adr2runtime += 1
    



def indirect_branch_miss_reduce(spe_pikle_file, map_file):
    # 对输入的元素块进行处理，每个块包含多个元素
    # 返回结果是每个进程处理的元素块的统计结果
    parsed_data:List[tuple] = pickle.load(open(spe_pikle_file, 'rb'))
    methods:List[analysis_codecache_segmented.CodeBlob] = analysis_codecache_segmented.parse_codecache(map_file)   
    start_address = methods[0].start_address - 100*1024*1024
    end_address = methods[-1].end_address + 100*1024*1024
    result = IndirectBranchMiss()
    runtime_result = IndirectMethon2Runtime()
    methodcall_result = MethodCall()
    lens = 0
    for element in parsed_data:
        pc = element[0]
        inst = element[1]
        event:str = element[2]
        target = element[3]

        if pc < start_address or pc > end_address:
            continue
        if target < start_address or target > end_address:
            continue

        caller_method = analysis_codecache_segmented.binary_search(methods, pc)
        callee_method = analysis_codecache_segmented.binary_search(methods, target)
        
        if caller_method == None or callee_method == None:
            continue
        # if caller_method.name == callee_method.name:
        #     continue
        statis_method_call(pc, inst, target, caller_method, callee_method, methodcall_result)
        if inst != "B IND":
            continue
        # if event.find("MISPRED") == -1:
        #     continue
        if caller_method.name == callee_method.name and caller_method.compile_level != 5:
            result.method_inter += 1
        elif caller_method.compile_level != 5 and callee_method.compile_level !=5 :
            result.method2method += 1
        elif caller_method.compile_level != 5 and callee_method.compile_level == 5:
            if callee_method.name.startswith("vtable"):
                result.method2vtable += 1
            else:
                result.method2runtime += 1
                if caller_method.in_stubcode(pc):
                    runtime_result.throuth_stubcode += 1
                else:
                    runtime_result.not_throuth_stubcode += 1
                runtime_result.update_hot_runtimecode(callee_method.name)
        elif caller_method.compile_level == 5 and callee_method.compile_level != 5:
            if caller_method.name.startswith("vtable"):
                result.vtable2method += 1
            else:
                result.runtime2method += 1
        else:
            result.other += 1

    return result,runtime_result,methodcall_result

def indirect_branch_miss_map(results):
    # 更新全局结果
    result = IndirectBranchMiss()
    runtime_result = IndirectMethon2Runtime()
    methodcall_result = MethodCall()
    for r,runtime_r,methodcall_r in results:
        result.add(r)
        runtime_result.merge_hot_runtimecode(runtime_r)
        methodcall_result.add(methodcall_r)
    result.print()
    runtime_result.print()
    methodcall_result.print()


def get_all_spe(directory):
    return [str(f) for f in Path(directory).rglob('*') if f.is_file()]

def process(spe_file, map_file):
    spes_list = get_all_spe(spe_file)
    
    # 创建一个进程池
    
    with Pool() as pool:

        # 使用 apply_async 函数和回调函数来并行处理块并消费结果
        
        results = pool.starmap(indirect_branch_miss_reduce, [(spe_pkl_file, map_file) for spe_pkl_file in spes_list])
        # for chunk in chunks:
        #     pool.apply_async(process_chunk, args=(chunk,methods,), callback=lambda x: update_result(result, x))

    indirect_branch_miss_map(results)

if __name__ == '__main__':
    # 这是要处理的列表
    carts2_spe_file = "/home/linwh/workspaces/light-jaco/spe/carts2-spes"
    carts2_map_file = "/home/linwh/workspaces/light-jaco/spe/carts2.jvm.codecache"

    buy2_spe_file = "/home/linwh/workspaces/light-jaco/spe/buy2-spes"
    buy2_map_file = "/home/linwh/workspaces/light-jaco/spe/buy2.jvm.codecache"

    print("buy2")
    process(buy2_spe_file, buy2_map_file)

    print("carts2")
    process(carts2_spe_file, carts2_map_file)

    
    
