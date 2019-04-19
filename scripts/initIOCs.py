# script for auto initialization of IOC from IOC_CONFIG file


import os
import re
import subprocess


def read_ioc_config():
    ioc_config_file = open("../configure/IOC_CONFIG", "r+")
    ioc_actions = []
    ioc_top = ""
    bin_top = ""

    line = ioc_config_file.readline()
    while line:
        if "IOC_DIR" in line:
            ioc_top = line.strip().split('=')[1]
        elif "TOP_BINARY_DIR" in line:
            bin_top = line.strip().split('=')[1]
        elif not line.startswith('#') and len(line) > 1:
            line = line.strip()
            line = re.sub(' +', ' ', line)
            action = line.split(' ')
            ioc_actions.append(action)
        line = ioc_config_file.readline()
    
    return ioc_actions, ioc_top, bin_top



def init_ioc_dir(ioc_top):
    if ioc_top == "":
        print("Error: IOC top not initialized")
        exit()
    elif os.path.exists(ioc_top) and os.path.isdir(ioc_top):
        print("IOC Dir already exits.")
    else:
        os.mkdir(ioc_top)
    


def getIOCBin(bin_top, ioc_type):
    driver_path = bin_top + "/areaDetector/" + ioc_type
    for name in os.listdir(driver_path):
        if "ioc" == name or "iocs" == name:
            driver_path = driver_path + "/" + name
            break
    for name in os.listdir(driver_path):
        if "IOC" in name or "ioc" in name:
            driver_path = driver_path + "/" + name
            break 
    driver_path = driver_path + "/bin"
    for name in os.listdir(driver_path):
        driver_path = driver_path + "/" + name
        break
    for name in os.listdir(driver_path):
        driver_path = driver_path + "/" + name
        break
    return driver_path



def perform_ioc_action(action, ioc_top, bin_top):
    out = subprocess.call(["git", "clone", "https://github.com/epicsNSLS2-deploy/ioc-template", ioc_top + "/" + action[1]])
    if out != 0:
        print("Error failed to clone IOC template for ioc {}".format(action[2]))
    else:
        print("Initializing IOC template for " + action[1])
        ioc_path = ioc_top +"/" + action[1]
        os.remove(ioc_path+"/st.cmd")

        startup_path = ioc_path+"/startupScripts"
        ioc_type = action[0][2:].lower()

        for file in os.listdir(ioc_path +"/startupScripts"):
            if ioc_type in file.lower():
                startup_path = startup_path + "/" + file
                break
        
        example_st = open(startup_path, "r+")
        st = open(ioc_path+"/st.cmd", "w+")

        line = example_st.readline()

        while line:
            if "#!" in line:
                st.write("#!"+bin_top + getIOCBin(bin_top, action[0]) + "\n")
            elif "envPaths" in line:
                st.write("< envPaths\n")
            else:
                st.write(line)

            line = example_st.readline()    


def init_iocs():
    actions, ioc_top, bin_top = read_ioc_config()
    init_ioc_dir(ioc_top)
    for action in actions:
        perform_ioc_action(action, ioc_top, bin_top)


init_iocs()



