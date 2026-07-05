import winreg

from rdp_cleaner.constants import DEFAULT_KEY, SERVERS_KEY, TSC_BASE
from rdp_cleaner.models import OperationResult

_KEY_RW = winreg.KEY_READ | winreg.KEY_SET_VALUE | winreg.KEY_CREATE_SUB_KEY


def _open_key(path: str, access: int = winreg.KEY_READ):
    return winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, access)


def _enum_values(key) -> list[tuple[str, object, int]]:
    values: list[tuple[str, object, int]] = []
    index = 0
    while True:
        try:
            values.append(winreg.EnumValue(key, index))
            index += 1
        except OSError:
            break
    return values


def _enum_subkeys(key) -> list[str]:
    subkeys: list[str] = []
    index = 0
    while True:
        try:
            subkeys.append(winreg.EnumKey(key, index))
            index += 1
        except OSError:
            break
    return subkeys


def get_mru_hosts() -> list[str]:
    try:
        with _open_key(DEFAULT_KEY) as key:
            return [
                str(value)
                for name, value, _ in _enum_values(key)
                if name.startswith("MRU") and name != "MRUIndex"
            ]
    except FileNotFoundError:
        return []


def get_server_hosts() -> list[str]:
    try:
        with _open_key(SERVERS_KEY) as key:
            return _enum_subkeys(key)
    except FileNotFoundError:
        return []


def clear_mru() -> OperationResult:
    deleted = 0
    try:
        with _open_key(DEFAULT_KEY, _KEY_RW) as key:
            names = [name for name, _, _ in _enum_values(key) if name.startswith("MRU")]
            for name in names:
                winreg.DeleteValue(key, name)
                deleted += 1
        return OperationResult(True, "已清除 MRU 连接记录", deleted)
    except FileNotFoundError:
        return OperationResult(True, "MRU 键不存在，无需清除", 0)
    except PermissionError:
        return OperationResult(False, "无权限修改注册表，请以当前用户运行", 0)
    except OSError as exc:
        return OperationResult(False, f"清除 MRU 失败: {exc}", deleted)


def _delete_tree(path: str) -> None:
    try:
        with _open_key(path, winreg.KEY_READ) as key:
            children = _enum_subkeys(key)
        for child in children:
            _delete_tree(rf"{path}\{child}")
    except FileNotFoundError:
        return
    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, path)


def _ensure_servers_key() -> None:
    with _open_key(TSC_BASE, _KEY_RW) as key:
        try:
            winreg.OpenKey(key, "Servers", 0, winreg.KEY_READ)
        except FileNotFoundError:
            winreg.CreateKey(key, "Servers")


def clear_servers() -> OperationResult:
    try:
        with _open_key(SERVERS_KEY, winreg.KEY_READ) as key:
            subkeys = _enum_subkeys(key)
    except FileNotFoundError:
        try:
            _ensure_servers_key()
            return OperationResult(True, "Servers 键不存在，已创建空键", 0)
        except OSError as exc:
            return OperationResult(False, f"创建 Servers 键失败: {exc}", 0)

    deleted = 0
    errors: list[str] = []
    for subkey in subkeys:
        try:
            _delete_tree(rf"{SERVERS_KEY}\{subkey}")
            deleted += 1
        except OSError as exc:
            errors.append(f"{subkey} ({exc})")

    try:
        _ensure_servers_key()
    except OSError:
        pass

    if errors:
        return OperationResult(
            False,
            f"部分 Servers 子键删除失败: {'; '.join(errors[:3])}",
            deleted,
        )
    return OperationResult(True, "已清除 Servers 主机记录", deleted)


def clear_registry() -> OperationResult:
    mru = clear_mru()
    servers = clear_servers()
    total = mru.count + servers.count
    if mru.success and servers.success:
        return OperationResult(True, f"{mru.message}; {servers.message}", total)

    messages = [result.message for result in (mru, servers) if not result.success]
    return OperationResult(False, "; ".join(messages), total)
