import os
from pathlib import Path

from rdp_cleaner.constants import JUMP_LIST_APP_ID
from rdp_cleaner.models import OperationResult


def get_default_rdp_path() -> Path:
    return Path.home() / "Documents" / "Default.rdp"


def get_jump_list_path() -> Path:
    appdata = os.environ.get("APPDATA", "")
    return Path(appdata) / "Microsoft" / "Windows" / "Recent" / "AutomaticDestinations" / JUMP_LIST_APP_ID


def default_rdp_exists() -> bool:
    return get_default_rdp_path().is_file()


def jump_list_exists() -> bool:
    return get_jump_list_path().is_file()


def clear_default_rdp() -> OperationResult:
    path = get_default_rdp_path()
    if not path.is_file():
        return OperationResult(True, "Default.rdp 不存在，无需清除", 0)
    try:
        path.unlink()
        return OperationResult(True, "已删除 Default.rdp", 1)
    except PermissionError:
        return OperationResult(False, "Default.rdp 被占用，请关闭远程桌面连接后重试", 0)
    except OSError as exc:
        return OperationResult(False, f"删除 Default.rdp 失败: {exc}", 0)


def clear_jump_list() -> OperationResult:
    path = get_jump_list_path()
    if not path.is_file():
        return OperationResult(True, "Jump List 文件不存在，无需清除", 0)
    try:
        path.unlink()
        return OperationResult(True, "已清除 Jump List 记录", 1)
    except PermissionError:
        return OperationResult(False, "Jump List 被资源管理器占用，请重启资源管理器或注销后重试", 0)
    except OSError as exc:
        return OperationResult(False, f"清除 Jump List 失败: {exc}", 0)
