import glob
import random
from libs.registry import RegistryDict


user_settings_reg_hive = RegistryDict("HKCU", r"Control Panel\Desktop")
windows_screensaver = random.choice(glob.glob((r"C:\Windows\system32\*.scr")))
reg_keys_and_set_values_dict = {
    "ScreenSaveActive": "1",
    "ScreenSaverIsSecure": "1",
    "ScreenSaveTimeOut": "120",
    "SCRNSAVE.EXE": f"{windows_screensaver}",
}


def module_setup():
    if not user_settings_reg_hive.exists():
        user_settings_reg_hive.create()
    for key, value in reg_keys_and_set_values_dict.items():
        user_settings_reg_hive.setitem(key, value)
    yield
    for key in reg_keys_and_set_values_dict:
        user_settings_reg_hive.setitem(key, "")
