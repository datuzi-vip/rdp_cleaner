import subprocess
import sys

from rdp_cleaner import credentials, files, registry
from rdp_cleaner.models import CleanOptions, CleanResult, OperationResult, PreviewResult, StepResult

_CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _run_hidden(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        creationflags=_CREATE_NO_WINDOW,
    )


def is_mstsc_running() -> bool:
    if sys.platform != "win32":
        return False
    result = _run_hidden(["tasklist", "/FI", "IMAGENAME eq mstsc.exe", "/NH"])
    return "mstsc.exe" in result.stdout.lower()


def kill_mstsc() -> OperationResult:
    if not is_mstsc_running():
        return OperationResult(True, "远程桌面连接未运行", 0)
    result = _run_hidden(["taskkill", "/IM", "mstsc.exe", "/F"])
    if result.returncode == 0:
        return OperationResult(True, "已关闭远程桌面连接进程", 1)
    return OperationResult(False, "无法关闭 mstsc.exe，请手动关闭后重试", 0)


def preview() -> PreviewResult:
    return PreviewResult(
        mru_hosts=registry.get_mru_hosts(),
        server_hosts=registry.get_server_hosts(),
        credentials=credentials.get_termsrv_credentials(),
        default_rdp_exists=files.default_rdp_exists(),
        jump_list_exists=files.jump_list_exists(),
    )


def format_preview(result: PreviewResult) -> str:
    lines = [
        "── 当前 RDP 连接记录预览 ──",
        "",
        f"MRU 最近连接 ({len(result.mru_hosts)} 条)",
    ]
    if result.mru_hosts:
        lines.extend(f"  · {host}" for host in result.mru_hosts)
    else:
        lines.append("  · 无记录")

    lines.extend(["", f"Servers 历史主机 ({len(result.server_hosts)} 个)"])
    if result.server_hosts:
        lines.extend(f"  · {host}" for host in result.server_hosts)
    else:
        lines.append("  · 无记录")

    lines.extend(
        [
            "",
            "本地痕迹",
            f"  · Default.rdp: {'存在' if result.default_rdp_exists else '不存在'}",
            f"  · Jump List: {'存在' if result.jump_list_exists else '不存在'}",
            "",
            f"TERMSRV 凭据 ({len(result.credentials)} 条)",
        ]
    )
    if result.credentials:
        lines.extend(f"  · {cred}" for cred in result.credentials)
    else:
        lines.append("  · 无记录")

    lines.extend(["", f"合计可清理项: {result.total_items}"])
    return "\n".join(lines)


def _append_step(result: CleanResult, name: str, operation: OperationResult) -> None:
    result.steps.append(
        StepResult(name=name, success=operation.success, message=operation.message, count=operation.count)
    )


def clean_all(options: CleanOptions) -> CleanResult:
    result = CleanResult()

    if options.kill_mstsc:
        operation = kill_mstsc()
        _append_step(result, "关闭 mstsc", operation)
        if not operation.success and is_mstsc_running():
            return result

    if options.clear_registry:
        _append_step(result, "清除注册表", registry.clear_registry())

    if options.clear_default_rdp:
        _append_step(result, "清除 Default.rdp", files.clear_default_rdp())

    if options.clear_jump_list:
        _append_step(result, "清除 Jump List", files.clear_jump_list())

    if options.clear_credentials:
        _append_step(result, "清除 TERMSRV 凭据", credentials.clear_termsrv_credentials())

    return result
