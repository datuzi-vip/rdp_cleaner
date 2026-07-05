import ctypes
from ctypes import wintypes

from rdp_cleaner.models import OperationResult

CREDENUMERATE_ALL_CREDENTIALS = 0x1

advapi32 = ctypes.windll.advapi32


class FILETIME(ctypes.Structure):
    _fields_ = [
        ("dwLowDateTime", wintypes.DWORD),
        ("dwHighDateTime", wintypes.DWORD),
    ]


class CREDENTIAL_ATTRIBUTEW(ctypes.Structure):
    pass


CREDENTIAL_ATTRIBUTEW._fields_ = [
    ("Keyword", wintypes.LPWSTR),
    ("Flags", wintypes.DWORD),
    ("ValueSize", wintypes.DWORD),
    ("Value", ctypes.POINTER(ctypes.c_byte)),
]


class CREDENTIALW(ctypes.Structure):
    pass


CREDENTIALW._fields_ = [
    ("Flags", wintypes.DWORD),
    ("Type", wintypes.DWORD),
    ("TargetName", wintypes.LPWSTR),
    ("Comment", wintypes.LPWSTR),
    ("LastWritten", FILETIME),
    ("CredentialBlobSize", wintypes.DWORD),
    ("CredentialBlob", ctypes.POINTER(ctypes.c_byte)),
    ("Persist", wintypes.DWORD),
    ("AttributeCount", wintypes.DWORD),
    ("Attributes", ctypes.POINTER(CREDENTIAL_ATTRIBUTEW)),
    ("TargetAlias", wintypes.LPWSTR),
    ("UserName", wintypes.LPWSTR),
]

PCREDENTIALW = ctypes.POINTER(CREDENTIALW)
PCREDENTIALW_PTR = ctypes.POINTER(PCREDENTIALW)


def _enumerate_termsrv() -> list[tuple[str, int]]:
    count = wintypes.DWORD()
    credentials_ptr = PCREDENTIALW_PTR()

    if not advapi32.CredEnumerateW(
        None,
        CREDENUMERATE_ALL_CREDENTIALS,
        ctypes.byref(count),
        ctypes.byref(credentials_ptr),
    ):
        return []

    items: list[tuple[str, int]] = []
    try:
        for i in range(count.value):
            cred = credentials_ptr[i].contents
            if cred.TargetName and cred.TargetName.upper().startswith("TERMSRV/"):
                items.append((cred.TargetName, cred.Type))
    finally:
        advapi32.CredFree(credentials_ptr)

    return items


def get_termsrv_credentials() -> list[str]:
    return [target for target, _ in _enumerate_termsrv()]


def clear_termsrv_credentials() -> OperationResult:
    items = _enumerate_termsrv()
    if not items:
        return OperationResult(True, "无 TERMSRV 凭据，无需清除", 0)

    deleted = 0
    errors: list[str] = []
    for target, cred_type in items:
        if advapi32.CredDeleteW(target, cred_type, 0):
            deleted += 1
        else:
            errors.append(target)

    if errors:
        return OperationResult(False, f"部分凭据删除失败: {', '.join(errors)}", deleted)
    return OperationResult(True, "已清除 TERMSRV 凭据", deleted)
