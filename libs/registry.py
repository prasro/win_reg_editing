import contextlib
import winreg
import itertools
import win32security


def checkIfBranchExists(hive, branch):
    """
    Deprecated, use "RegistryDict().exists()"
    """
    try:
        with RegKey(hive, branch, "read", extra_flags=0):
            return True
    except RuntimeAndKeyError:
        return False


def checkIfKeyExists(hive, branch, key):
    """
    Deprecated, use "key in RegistryDict()"
    """
    try:
        return key in RegistryDict(hive, branch)
    except RuntimeAndKeyError:
        return False


def createBranch(hive, branch):
    try:
        with RegKey(hive, branch, "create", extra_flags=0):
            return True
    except RuntimeAndKeyError:
        return False


def getRegistryValue(hive, branch, value_name, default_value=None):
    with contextlib.suppress(RuntimeAndKeyError):
        registry_key = RegistryDict.wow64_32(hive, branch)
        return registry_key.get(value_name, default_value)
    return default_value


def setRegistryValue(hive, branch, value_name, value):
    registry_key = RegistryDict.wow64_32(hive, branch)
    registry_key[value_name] = value


def _wrap_call(call, key, i):
    try:
        return call(key, i)
    except WindowsError:
        return None


def enum_key(key, i):
    return _wrap_call(winreg.EnumKey, key, i)


def enum_value(key, i):
    return _wrap_call(winreg.EnumValue, key, i)


class RuntimeAndKeyError(RuntimeError, KeyError):
    contextlib.suppress(RuntimeError, KeyError)


class RegKey:

    hivemap = {
        "HKLM": winreg.HKEY_LOCAL_MACHINE,
        "HKCU": winreg.HKEY_CURRENT_USER,
        "HKCR": winreg.HKEY_CLASSES_ROOT,
        "HKCC": winreg.HKEY_CURRENT_CONFIG,
        "HKU": winreg.HKEY_USERS,
        "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
        "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
        "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
        "HKEY_CURRENT_CONFIG": winreg.HKEY_CURRENT_CONFIG,
        "HKEY_USERS": winreg.HKEY_USERS,
    }


class RegistryDict(object):
    DACL_SECURITY_INFORMATION = win32security.DACL_SECURITY_INFORMATION
    OWNER_SECURITY_INFORMATION = win32security.OWNER_SECURITY_INFORMATION

    @property
    def branch(self):
        return self.__branch

    def __repr__(self):
        return f"RegistryDict('{self.__hive}', r'{self.__branch}')"

    def get_subkeys(self, key):
        ret = []
        counter = itertools.count()
        while item := enum_key(key, next(counter)):
            ret.append(item)
        return ret

    def items(self) -> list:
        ret = []
        with RegKey(
            self.__hive, self.__branch, "read", extra_flags=self.__extra_flags
        ) as key:
            counter = itertools.count()
            while item := enum_value(key, next(counter)):
                ret.append((item[0], item[1]))
        return ret

    def subkeys(self):
        """
        Returns a list of subkey dicts
        """
        with RegKey(
            self.__hive, self.__branch, "read", extra_flags=self.__extra_flags
        ) as hk:
            subkeys = self.get_subkeys(hk)
        return [
            RegistryDict(self.__hive, self.__branch + "\\" + key, self.__extra_flags)
            for key in subkeys
        ]

    def wipe_recursive(self, key):
        # Get subkeys
        with RegKey(self.__hive, key, "read", extra_flags=self.__extra_flags) as hk:
            subkeys = self.get_subkeys(hk)
        # Remove subkeys (recursively)
        for sub in subkeys:
            self.wipe_recursive(key + "\\" + sub)
        # Remove self
        winreg.DeleteKey(RegKey.hivemap[self.__hive], key)

    def wipe(self):
        # Have to remove subkeys recursively
        self.wipe_recursive(self.__branch)

    def all_subkeys(self):
        """
        Returns a list of all subkey dicts
        """
        for subkey in self.subkeys():
            yield subkey
            yield from subkey.all_subkeys()

    def setitem(self, key, value, reg_type=None):
        with RegKey(
            self.__hive, self.__branch, "create", extra_flags=self.__extra_flags
        ) as k:
            try:
                if reg_type:
                    winreg.SetValueEx(k, key, 0, reg_type, value)
                elif isinstance(value, int):
                    winreg.SetValueEx(k, key, 0, winreg.REG_DWORD, value)
                elif isinstance(value, (tuple, list)):
                    winreg.SetValueEx(k, key, 0, winreg.REG_MULTI_SZ, value)
                else:
                    winreg.SetValueEx(k, key, 0, winreg.REG_SZ, value)
            except WindowsError as e:
                raise RuntimeAndKeyError(
                    f"Failed to write registry key '{key}' ({e})"
                ) from e

    def exists(self):
        try:
            with RegKey(
                self.__hive, self.__branch, "read", extra_flags=self.__extra_flags
            ):
                return True
        except RuntimeAndKeyError:
            return False

    def create(self):
        try:
            with RegKey(
                self.__hive, self.__branch, "create", extra_flags=self.__extra_flags
            ):
                return True
        except RuntimeAndKeyError:
            return False
