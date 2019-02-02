#
# File that updates the release file in support/configure/RELEASE used 
# in the next compilation step
#
#


import os
import read_install_config
import ad_config_setup


def nuke_dev_stats_release(path_to_dev_stats):
    os.rename(path_to_dev_stats+"/configure/RELEASE", path_to_dev_stats+"/configure/RELEASE_OLD")
    new_release = open(path_to_dev_stats+"/configure/RELEASE", "w+")
    new_release.write("EPICS_BASE=.\n")
    new_release.write("SUPPORT=.\n")
    new_release.write("SNCSEQ=.\n")
    new_release.write("-include $(SUPPORT)/configure/EPICS_BASE.$(EPICS_HOST_ARCH)\n")


def update_ad_releases(module_list, path_to_ad):
    print("Updating AD Releases\n")
    macro_val_pairs = []
    for module in module_list:
        # print("{}={}".format(module[0], module[2]))
        macro_val_pairs.append([module[0], module[2]])
    ad_config_setup.update_ad_releases(path_to_ad, macro_val_pairs)
    


def update_release_file():
    module_list, install_location = read_install_config.read_install_config_file(update_path=False)
    config_mod = []
    for module in module_list:
        if module[0] == "SUPPORT" or module[0] == "EPICS_BASE":
            module[2] = read_install_config.expand_module_path(module[2], module_list, install_location)
        elif module[0] == "CONFIGURE":
            config_mod = module
        elif module[0] == "DEVIOCSTATS":
            module[2] = read_install_config.expand_module_path(module[2], module_list, install_location)
            nuke_dev_stats_release(module[2])
        elif module[0] == "AREA_DETECTOR":
            path_to_ad = read_install_config.expand_module_path(module[2], module_list, install_location)
            update_ad_releases(module_list, path_to_ad)


    config_mod[2] = read_install_config.expand_module_path(config_mod[2], module_list, install_location)

    path_to_release = config_mod[2] + "/" + "RELEASE"
    path_to_old_release = config_mod[2] + "/" + "RELEASE_OLD"
    os.rename(path_to_release, path_to_old_release)

    old_file = open(path_to_old_release, "r")
    new_file = open(path_to_release, "w")
    written_mod = []
    line = old_file.readline()
    while line:
        if "=" in line:
            mod_found = False
            for module in module_list:
                if module[0] == line.split("=")[0]:
                    if module[0] == "AREA_DETECTOR" or module[0] == "ADCORE" or module[4] == "NO":
                        new_file.write("#"+ module[0]+"="+module[2]+"\n")
                        written_mod.append(module[0])
                    else:
                        new_file.write(module[0] + "=" + module[2] + "\n")
                        written_mod.append(module[0])
                    mod_found = True
            if not mod_found:
                new_file.write("#" + line)
                written_mod.append(line.split('=')[0])
        else:
            new_file.write(line)
            
        line = old_file.readline()
    
    for module in module_list:
        was_written = False
        for written_module in written_mod:
            if module[0] == written_module:
                was_written = True
        if not was_written:
            if module[0] != "CONFIGURE" and module[0] != "UTILS" and module[0] != "DOCUMENTATION":
                new_file.write("#" + module[0]+"="+module[2]+"\n")
                    
    old_file.close()
    new_file.close()

update_release_file()