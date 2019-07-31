"""
File containing helper functions for installSynApps unit testing
"""

__author__      = "Jakub Wlodek"
__copyright__   = "Copyright June 2019, Brookhaven Science Associates"


def compare_mod(compare_module_1, compare_module_2):
    """ Function for comparing two install modules """

    if compare_module_1.name       != compare_module_2.name:
        return False
    if compare_module_1.version    != compare_module_2.version:
        return False
    if compare_module_1.rel_path   != compare_module_2.rel_path:
        return False
    if compare_module_1.abs_path   != compare_module_2.abs_path:
        return False
    if compare_module_1.url_type   != compare_module_2.url_type:
        return False
    if compare_module_1.url        != compare_module_2.url:
        return False
    if compare_module_1.repository != compare_module_2.repository:
        return False
    if compare_module_1.clone      != compare_module_2.clone:
        return False
    if compare_module_1.build      != compare_module_2.build:
        return False
    return True


def compare_files(fp1, fp2):
    """
    Function that compares two target files

    Parameters
    ----------
    fp1 : open file pointer
        pointer to open first file
    fp2 : open file pointer
        pointer to open second file
    
    Returns
    -------
    True if they are the same, false otherwise
    """

    line1 = fp1.readline()
    line2 = fp2.readline()

    while line1 and line2:
        if not line1 == line2:
            return False
        
        line1 = fp1.readline()
        line2 = fp2.readline()

    if line1 or line2:
        return False

    return True