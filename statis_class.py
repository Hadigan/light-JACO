

class IndirectBranchMiss():
    def __init__(self) -> None:
        self.method2method = 0
        self.method2vtable = 0
        self.method2runtime = 0
        self.vtable2method = 0
        self.runtime2other = 0
        self.runtime2method = 0
        self.other = 0
        self.method_inter = 0
        self.vtable2runtime = 0
        self.runtime2vtable = 0
        self.runtime2runtime = 0
    
    def add(self, other_data):
        for attribution_name, value in self.__dict__.items():
            setattr(self, attribution_name, value + getattr(other_data, attribution_name))
    
    def print(self):

        total = 0
        for attribution_name, value in self.__dict__.items():
            total += value
        
        for attribution_name, value in self.__dict__.items():
            print(f"{attribution_name}:\t{value/total}")

class IndirectMethon2Runtime():
    def __init__(self) -> None:
        self.throuth_stubcode = 0
        self.not_throuth_stubcode = 0
        self.hot_runtimecode = {}

    def add(self, other_data):
        for attribution_name, value in self.__dict__.items():
            setattr(self, attribution_name, value + getattr(other_data, attribution_name))
    
    def print(self):

        total = self.throuth_stubcode + self.not_throuth_stubcode + 1
        print(f"call throuth stubcode:\t{self.throuth_stubcode/total}")
        sorted_hotruntime = sorted(self.hot_runtimecode.items(), key=lambda item: item[1], reverse=True)[0:10]
        for name,count in sorted_hotruntime:
            print(f"runtime code:{name}\tcount:{count/total}")
    
    def update_hot_runtimecode(self, runtimecode_name):
        if runtimecode_name not in self.hot_runtimecode:
            self.hot_runtimecode[runtimecode_name] = 0
        self.hot_runtimecode[runtimecode_name] += 1
    
    def merge_hot_runtimecode(self, otherdata):
        self.throuth_stubcode += otherdata.throuth_stubcode
        self.not_throuth_stubcode += otherdata.not_throuth_stubcode
        for runtime_name in otherdata.hot_runtimecode:
            if runtime_name not in self.hot_runtimecode:
                self.hot_runtimecode[runtime_name] = 0
            self.hot_runtimecode[runtime_name] += otherdata.hot_runtimecode[runtime_name]
    

class MethodCall():
    def __init__(self) -> None:
        self.BL2vtable = 0
        self.BL2stubroutine = 0
        self.BL2method = 0
        self.BL2runtime = 0
        self.BL2stub = 0
        self.stub2vtable = 0
        self.stub2method = 0
        self.stub2stubroutine = 0
        self.stub2runtime = 0
        self.adr2runtime = 0
        self.direct2method = 0
        self.vtable = 0
        self.stubroutine = 0
        self.runtime = 0
        self.other = 0
    
    def add(self, other_data):
        for attribution_name, value in self.__dict__.items():
            setattr(self, attribution_name, value + getattr(other_data, attribution_name))
    
    def print(self):

        total = 0
        for attribution_name, value in self.__dict__.items():
            total += value
        
        for attribution_name, value in self.__dict__.items():
            print(f"{attribution_name}:\t{value/total}")

        total_method_call = 0
        total_method_call += self.BL2method
        total_method_call += self.BL2runtime
        total_method_call += self.BL2stubroutine
        total_method_call += self.BL2vtable

        total_method_call += self.stub2method
        total_method_call += self.stub2runtime
        total_method_call += self.stub2vtable
        total_method_call += self.stub2stubroutine

        total_method_call += self.adr2runtime
        
        self.direct2method = (self.BL2method + self.stub2method)/total_method_call
        self.vtable = (self.BL2vtable + self.stub2vtable)/total_method_call
        self.stubroutine = (self.BL2stubroutine + self.stub2stubroutine)/total_method_call
        self.runtime = (self.BL2runtime + self.stub2runtime + self.adr2runtime)/total_method_call

        print(f"direct2method: {self.direct2method}")
        print(f"\tdirect2method-trampoline: {self.stub2method/(self.BL2method + self.stub2method)}")
        print(f"vtable: {self.vtable}")
        print(f"\tvtable-trampoline: {self.stub2vtable/(self.BL2vtable + self.stub2vtable)}")
        print(f"stubroutines: {self.stubroutine}")
        print(f"\tstubroutines-trampoline: {self.stub2stubroutine/(self.BL2stubroutine + self.stub2stubroutine)}")
        print(f"runtime: {self.runtime}")
        print(f"\truntime-adr: {self.adr2runtime/(self.BL2runtime + self.stub2runtime + self.adr2runtime)}")

        print(f"total-trampoline: {(self.stub2method+self.stub2runtime+self.stub2stubroutine+self.stub2vtable) / total_method_call}")




