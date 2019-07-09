"""
Class responsible for packaging compiled binaries based on install config
"""


import os
import shutil
from sys import platform
import platform as p
import datetime
import time
import subprocess
import installSynApps.DataModel.install_config as IC

class Packager:


    def __init__(self, install_config, ad_drivers, opt_modules, force_arch=None):
        self.install_config = install_config

        self.ad_drivers = ad_drivers
        self.opt_modules = opt_modules
        if force_arch is not None:
            self.arch = force_arch
            self.OS = force_arch
        elif platform == 'linux':
            v = p.linux_distribution()
            if len(v[0]) > 0 and len(v[1]) > 0:
                self.OS = '{}_{}'.format(v[0], v[1])
            else:
                self.OS = 'linux-x86_64'
            self.arch = 'linux-x86_64'
        elif platform == 'win32':
            self.arch = 'windows-x64-static'
            self.OS = self.arch
        self.start_time = 0


    def start_timer(self):
        self.start_time = time.time()


    def stop_timer(self):
        end_time = time.time()
        return end_time - self.start_time


    def grab_folder(self, src, dest):
        if os.path.exists(src):
            shutil.copytree(src, dest)


    def grab_base(self, top):
        base_path = self.install_config.base_path
        self.grab_folder(base_path + '/bin/' + self.arch,   top + '/base/bin/' + self.arch)
        self.grab_folder(base_path + '/lib/' + self.arch,   top + '/base/lib/' + self.arch)
        self.grab_folder(base_path + '/lib/perl',           top + '/base/lib/perl')
        self.grab_folder(base_path + '/configure',          top + '/base/configure')
        self.grab_folder(base_path + '/include',            top + '/base/include')
        self.grab_folder(base_path + '/startup',            top + '/base/startup')


    def grab_module(self, top, module_name, module_location, is_ad_module = False):
        self.grab_folder(module_location + '/' + module_name + '/opi', top + '/' + module_name +'/opi')
        self.grab_folder(module_location + '/' + module_name + '/db', top + '/' + module_name +'/db')
        self.grab_folder(module_location + '/' + module_name + '/include', top + '/' + module_name +'/include')
        self.grab_folder(module_location + '/' + module_name + '/bin/' + self.arch, top + '/' + module_name +'/bin/' + self.arch)
        self.grab_folder(module_location + '/' + module_name + '/lib/' + self.arch, top + '/' + module_name +'/lib/' + self.arch)
        self.grab_folder(module_location + '/' + module_name + '/configure', top + '/' + module_name +'/configure')
        self.grab_folder(module_location + '/' + module_name + '/iocBoot', top + '/' + module_name +'/iocBoot')
        for dir in os.listdir(module_location + '/' + module_name):
            if 'App' in dir and not dir.startswith('test'):
                self.grab_folder(module_location + '/' + module_name + '/' + dir + '/Db', top + '/' + module_name +'/' + dir + '/Db')
                self.grab_folder(module_location + '/' + module_name + '/' + dir + '/op', top + '/' + module_name +'/' + dir + '/op')
        if is_ad_module:
            if os.path.exists(module_location + '/' + module_name + '/iocs'):
                for dir in os.listdir(module_location + '/' + module_name + '/iocs'):
                    if 'IOC' in dir:
                        self.grab_folder(module_location + '/' + module_name + '/' + dir + '/bin/' + self.arch, top + '/' + module_name + '/' + dir + '/bin/' + self.arch)
                        self.grab_folder(module_location + '/' + module_name + '/' + dir + '/lib/' + self.arch, top + '/' + module_name + '/' + dir + '/lib/' + self.arch)
                        self.grab_folder(module_location + '/' + module_name + '/' + dir + '/dbd', top + '/' + module_name + '/' + dir + '/dbd')
                        self.grab_folder(module_location + '/' + module_name + '/' + dir + '/iocBoot', top + '/' + module_name + '/' + dir + '/iocBoot')


    def grab_support(self, top):
        support_path = self.install_config.support_path
        support_modules = ['asyn', 'autosave', 'busy', 'calc', 'iocStats', 'seq', 'sscan']
        if self.opt_modules is not None:
            support_modules = support_modules.extend(self.opt_modules)
        for module in support_modules:
            self.grab_module(top, module, support_path)


    def grab_ad(self, top):
        ad_path = self.install_config.ad_path
        self.grab_folder(ad_path + '/ADCore/db',        top + '/areaDetector/ADCore/db')
        self.grab_folder(ad_path + '/ADCore/ADApp/Db',        top + '/areaDetector/ADCore/ADApp/Db')
        self.grab_folder(ad_path + '/ADCore/ADApp/op',        top + '/areaDetector/ADCore/ADApp/op')
        self.grab_folder(ad_path + '/ADCore/iocBoot',   top + '/areaDetector/ADCore/iocBoot')
        self.grab_folder(ad_path + '/ADViewers/ImageJ',        top + '/areaDetector/ADViewers/ImageJ')
        self.grab_folder(ad_path + '/ADCore/bin/' + self.arch,        top + '/areaDetector/ADCore/bin/' + self.arch)
        self.grab_folder(ad_path + '/ADCore/lib/' + self.arch,          top + '/areaDetector/ADCore/lib/' + self.arch)
        self.grab_folder(ad_path + '/ADSupport/bin/' + self.arch,        top + '/areaDetector/ADSupport/bin/' + self.arch)
        self.grab_folder(ad_path + '/ADSupport/lib/' + self.arch,          top + '/areaDetector/ADSupport/lib/' + self.arch)
        if self.ad_drivers is not None:
            for driver in self.ad_drivers:
                self.grab_module(top + '/areaDetector', driver, ad_path)




    def create_tarball(self, filename):
        os.mkdir('temp')
        readme_fp = open('DEPLOYMENTS/README_{}.txt'.format(filename), 'w')
        readme_fp.write('{}\n\n'.format(filename))
        readme_fp.write('Versions used in this deployment:\n')
        readme_fp.write('[folder name] : [git tag]\n\n')

        self.grab_base('temp')
        self.grab_support('temp')
        self.grab_ad('temp')
        out = subprocess.call(['tar', 'czf', filename + '.tgz', '-C', 'temp', '.'])
        if out < 0:
            return out
        os.rename(filename + '.tgz', 'DEPLOYMENTS/' + filename + '.tgz')
        shutil.rmtree('temp')
        readme_fp.close()
        return out


    def create_package(self):
        if not os.path.exists('DEPLOYMENTS'):
            os.mkdir('DEPLOYMENTS')
        date_str = datetime.date.today()
        output_filename = 'NSLS2_AD_{}_Bin_{}_{}'.format(self.install_config.get_core_version(), self.OS, date_str)
        self.start_timer()
        status = self.create_tarball(output_filename)
        elapsed = self.stop_timer()
        if status < 0:
            return status
        else:
            print('Done. Tarring took {} seconds.'.format(elapsed))
            return elapsed
