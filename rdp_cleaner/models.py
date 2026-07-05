from dataclasses import dataclass, field


@dataclass
class OperationResult:
    success: bool
    message: str
    count: int = 0


@dataclass
class StepResult:
    name: str
    success: bool
    message: str
    count: int = 0


@dataclass
class CleanOptions:
    clear_registry: bool = True
    clear_default_rdp: bool = True
    clear_jump_list: bool = True
    clear_credentials: bool = False
    kill_mstsc: bool = True


@dataclass
class PreviewResult:
    mru_hosts: list[str] = field(default_factory=list)
    server_hosts: list[str] = field(default_factory=list)
    credentials: list[str] = field(default_factory=list)
    default_rdp_exists: bool = False
    jump_list_exists: bool = False

    @property
    def file_count(self) -> int:
        return int(self.default_rdp_exists) + int(self.jump_list_exists)

    @property
    def total_items(self) -> int:
        return len(self.mru_hosts) + len(self.server_hosts) + len(self.credentials) + self.file_count

    @property
    def is_empty(self) -> bool:
        return self.total_items == 0


@dataclass
class CleanResult:
    steps: list[StepResult] = field(default_factory=list)

    @property
    def all_success(self) -> bool:
        return all(step.success for step in self.steps)

    @property
    def cleared_count(self) -> int:
        return sum(step.count for step in self.steps if step.success)

    def summary(self) -> str:
        lines = []
        for step in self.steps:
            status = "成功" if step.success else "失败"
            detail = f" ({step.count} 项)" if step.count else ""
            lines.append(f"[{status}] {step.name}{detail}: {step.message}")
        return "\n".join(lines)
