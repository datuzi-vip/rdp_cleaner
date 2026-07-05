import threading
import tkinter.messagebox as messagebox

import customtkinter as ctk

from rdp_cleaner import __version__
from rdp_cleaner.cleaner import clean_all, format_preview, preview
from rdp_cleaner.constants import APP_SUBTITLE, APP_TITLE
from rdp_cleaner.models import CleanOptions, PreviewResult
from rdp_cleaner.ui import theme as t


class StatCard(ctk.CTkFrame):
    def __init__(self, master, label: str, color_key: str):
        super().__init__(
            master,
            corner_radius=t.CORNER_RADIUS_SM,
            fg_color=t.STAT_COLORS[color_key],
            border_width=1,
            border_color=t.CARD_BORDER_LIGHT,
        )
        self.value_label = ctk.CTkLabel(self, text="—", font=t.FONT_STAT)
        self.value_label.pack(pady=(10, 0))
        ctk.CTkLabel(self, text=label, font=t.FONT_STAT_LABEL, text_color=t.MUTED).pack(pady=(0, 10))

    def set_value(self, value: int | str) -> None:
        self.value_label.configure(text=str(value))


class OptionRow(ctk.CTkFrame):
    def __init__(self, master, title: str, description: str, variable: ctk.BooleanVar):
        super().__init__(
            master,
            corner_radius=t.CORNER_RADIUS_SM,
            fg_color=t.CARD_LIGHT,
            border_width=1,
            border_color=t.CARD_BORDER_LIGHT,
        )
        self.grid_columnconfigure(1, weight=1)

        self.checkbox = ctk.CTkCheckBox(
            self,
            text="",
            variable=variable,
            width=24,
            checkbox_width=22,
            checkbox_height=22,
            corner_radius=6,
            border_width=2,
        )
        self.checkbox.grid(row=0, column=0, rowspan=2, padx=(14, 8), pady=14, sticky="n")

        ctk.CTkLabel(self, text=title, font=t.FONT_BODY, anchor="w").grid(
            row=0, column=1, sticky="w", pady=(12, 0)
        )
        ctk.CTkLabel(
            self,
            text=description,
            font=t.FONT_CAPTION,
            text_color=t.MUTED,
            anchor="w",
            wraplength=360,
            justify="left",
        ).grid(row=1, column=1, sticky="w", pady=(2, 12))

        self.badge = ctk.CTkLabel(
            self,
            text="0",
            width=36,
            height=24,
            corner_radius=12,
            fg_color=("gray85", "gray25"),
            font=t.FONT_CAPTION,
        )
        self.badge.grid(row=0, column=2, rowspan=2, padx=14, pady=14)

    def set_count(self, count: int) -> None:
        self.badge.configure(text=str(count))


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.title(APP_TITLE)
        self.geometry("680x720")
        self.minsize(620, 660)
        self.configure(fg_color=t.SURFACE_LIGHT)

        self.var_registry = ctk.BooleanVar(value=True)
        self.var_default_rdp = ctk.BooleanVar(value=True)
        self.var_jump_list = ctk.BooleanVar(value=True)
        self.var_credentials = ctk.BooleanVar(value=False)

        self._preview_data: PreviewResult | None = None
        self._build_ui()
        self.after(300, self._refresh_preview_async)

    def _build_ui(self) -> None:
        root = ctk.CTkFrame(self, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=24, pady=20)
        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(4, weight=1)

        self._build_header(root)
        self._build_stats(root)
        self._build_options(root)
        self._build_actions(root)
        self._build_log(root)
        self._build_footer(root)

    def _build_header(self, parent) -> None:
        header = ctk.CTkFrame(
            parent,
            corner_radius=t.CORNER_RADIUS,
            fg_color=t.HEADER_LIGHT,
            border_width=1,
            border_color=t.CARD_BORDER_LIGHT,
        )
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        header.grid_columnconfigure(1, weight=1)

        icon = ctk.CTkLabel(
            header,
            text="🖥",
            font=("Segoe UI Emoji", 28),
            width=56,
        )
        icon.grid(row=0, column=0, rowspan=2, padx=(18, 8), pady=16)

        ctk.CTkLabel(header, text=APP_TITLE, font=t.FONT_TITLE, anchor="w").grid(
            row=0, column=1, sticky="w", pady=(16, 0)
        )
        ctk.CTkLabel(
            header,
            text=APP_SUBTITLE,
            font=t.FONT_SUBTITLE,
            text_color=t.MUTED,
            anchor="w",
        ).grid(row=1, column=1, sticky="w", pady=(2, 16))

    def _build_stats(self, parent) -> None:
        stats = ctk.CTkFrame(parent, fg_color="transparent")
        stats.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        for i in range(4):
            stats.grid_columnconfigure(i, weight=1, uniform="stat")

        self.stat_mru = StatCard(stats, "MRU 连接", "mru")
        self.stat_mru.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.stat_servers = StatCard(stats, "历史主机", "servers")
        self.stat_servers.grid(row=0, column=1, sticky="ew", padx=6)

        self.stat_files = StatCard(stats, "本地文件", "files")
        self.stat_files.grid(row=0, column=2, sticky="ew", padx=6)

        self.stat_creds = StatCard(stats, "保存凭据", "creds")
        self.stat_creds.grid(row=0, column=3, sticky="ew", padx=(6, 0))

    def _build_options(self, parent) -> None:
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        section.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(section, text="清除选项", font=t.FONT_SECTION, anchor="w").grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )

        options = ctk.CTkFrame(section, fg_color="transparent")
        options.grid(row=1, column=0, sticky="ew")
        options.grid_columnconfigure(0, weight=1)

        self.row_registry = OptionRow(
            options,
            "连接历史",
            "清除注册表 MRU 最近连接与 Servers 历史主机记录",
            self.var_registry,
        )
        self.row_registry.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self.row_default_rdp = OptionRow(
            options,
            "Default.rdp",
            "删除文档目录中的默认远程桌面配置文件",
            self.var_default_rdp,
        )
        self.row_default_rdp.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        self.row_jump_list = OptionRow(
            options,
            "Jump List",
            "清除任务栏与开始菜单中的远程桌面快捷记录",
            self.var_jump_list,
        )
        self.row_jump_list.grid(row=2, column=0, sticky="ew", pady=(0, 8))

        self.row_credentials = OptionRow(
            options,
            "RDP 凭据",
            "删除凭据管理器中的 TERMSRV 保存密码（敏感操作）",
            self.var_credentials,
        )
        self.row_credentials.grid(row=3, column=0, sticky="ew")

    def _build_actions(self, parent) -> None:
        actions = ctk.CTkFrame(parent, fg_color="transparent")
        actions.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        actions.grid_columnconfigure(0, weight=1)

        self.btn_preview = ctk.CTkButton(
            actions,
            text="刷新预览",
            command=self._refresh_preview_async,
            height=40,
            corner_radius=t.CORNER_RADIUS_SM,
            font=t.FONT_BODY,
            fg_color=("gray78", "gray28"),
            hover_color=("gray70", "gray34"),
            text_color=("gray20", "gray90"),
        )
        self.btn_preview.grid(row=0, column=0, sticky="w")

        self.btn_clean = ctk.CTkButton(
            actions,
            text="一键清除",
            command=self._on_clean,
            height=40,
            width=140,
            corner_radius=t.CORNER_RADIUS_SM,
            font=t.FONT_BODY,
            fg_color=t.DANGER,
            hover_color=t.DANGER_HOVER,
        )
        self.btn_clean.grid(row=0, column=1, sticky="e")

    def _build_log(self, parent) -> None:
        panel = ctk.CTkFrame(
            parent,
            corner_radius=t.CORNER_RADIUS,
            fg_color=t.LOG_LIGHT,
            border_width=1,
            border_color=t.CARD_BORDER_LIGHT,
        )
        panel.grid(row=4, column=0, sticky="nsew", pady=(0, 12))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(panel, text="操作日志", font=t.FONT_SECTION, anchor="w").grid(
            row=0, column=0, sticky="w", padx=16, pady=(14, 6)
        )

        self.log_box = ctk.CTkTextbox(
            panel,
            font=t.FONT_MONO,
            corner_radius=t.CORNER_RADIUS_SM,
            fg_color=("white", "#111827"),
            border_width=1,
            border_color=t.CARD_BORDER_LIGHT,
            wrap="word",
        )
        self.log_box.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self._log("就绪。正在扫描当前 RDP 连接记录…")

    def _build_footer(self, parent) -> None:
        footer = ctk.CTkFrame(parent, fg_color="transparent")
        footer.grid(row=5, column=0, sticky="ew")
        footer.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            footer,
            text="等待扫描",
            font=t.FONT_CAPTION,
            text_color=t.MUTED,
            anchor="w",
        )
        self.status_label.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            footer,
            text=f"v{__version__}",
            font=t.FONT_CAPTION,
            text_color=t.MUTED,
            anchor="e",
        ).grid(row=0, column=1, sticky="e")

    def _log(self, text: str) -> None:
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")

    def _set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        self.btn_preview.configure(state=state)
        self.btn_clean.configure(state=state)

    def _update_stats(self, data: PreviewResult) -> None:
        registry_count = len(data.mru_hosts) + len(data.server_hosts)
        self.stat_mru.set_value(len(data.mru_hosts))
        self.stat_servers.set_value(len(data.server_hosts))
        self.stat_files.set_value(data.file_count)
        self.stat_creds.set_value(len(data.credentials))

        self.row_registry.set_count(registry_count)
        self.row_default_rdp.set_count(int(data.default_rdp_exists))
        self.row_jump_list.set_count(int(data.jump_list_exists))
        self.row_credentials.set_count(len(data.credentials))

        if data.is_empty:
            self.status_label.configure(text="未发现可清理的 RDP 记录", text_color=t.SUCCESS)
        else:
            self.status_label.configure(
                text=f"发现 {data.total_items} 项可清理记录",
                text_color=t.WARNING,
            )

    def _apply_preview(self, data: PreviewResult) -> None:
        self._preview_data = data
        self._update_stats(data)
        self.log_box.delete("1.0", "end")
        self._log(format_preview(data))

    def _refresh_preview_async(self) -> None:
        self._set_busy(True)
        self.status_label.configure(text="正在扫描…", text_color=t.MUTED)

        def run() -> None:
            try:
                data = preview()
                self.after(0, lambda: self._on_preview_done(data))
            except Exception as exc:
                self.after(0, lambda: self._on_preview_error(str(exc)))

        threading.Thread(target=run, daemon=True).start()

    def _on_preview_done(self, data: PreviewResult) -> None:
        self._set_busy(False)
        self._apply_preview(data)

    def _on_preview_error(self, error: str) -> None:
        self._set_busy(False)
        self.status_label.configure(text="扫描失败", text_color=t.DANGER)
        self._log(f"扫描失败: {error}")

    def _get_options(self) -> CleanOptions:
        return CleanOptions(
            clear_registry=self.var_registry.get(),
            clear_default_rdp=self.var_default_rdp.get(),
            clear_jump_list=self.var_jump_list.get(),
            clear_credentials=self.var_credentials.get(),
        )

    def _on_clean(self) -> None:
        options = self._get_options()
        if not any(
            [
                options.clear_registry,
                options.clear_default_rdp,
                options.clear_jump_list,
                options.clear_credentials,
            ]
        ):
            messagebox.showwarning("提示", "请至少选择一项清除内容。")
            return

        if options.clear_credentials:
            if not messagebox.askyesno(
                "确认删除凭据",
                "将删除 Windows 凭据管理器中所有 TERMSRV 保存的密码。\n\n确定继续吗？",
            ):
                return

        if not messagebox.askyesno(
            "确认清除",
            "确定要清除选中的 RDP 连接记录吗？\n此操作不可撤销。",
        ):
            return

        self._set_busy(True)
        self.status_label.configure(text="正在清除…", text_color=t.MUTED)
        self._log("\n── 开始清除 ──")

        def run() -> None:
            try:
                result = clean_all(options)
                self.after(0, lambda: self._on_clean_done(result))
            except Exception as exc:
                self.after(0, lambda: self._on_clean_error(str(exc)))

        threading.Thread(target=run, daemon=True).start()

    def _on_clean_done(self, result) -> None:
        self._set_busy(False)
        self._log(result.summary())
        if result.all_success:
            self._log(f"\n清除完成，共处理 {result.cleared_count} 项。")
            self._log("若 Jump List 仍显示旧记录，请重启资源管理器或重新打开 mstsc。")
            messagebox.showinfo("完成", "RDP 连接记录已清除。")
            self._refresh_preview_async()
        else:
            self.status_label.configure(text="部分清除失败", text_color=t.DANGER)
            messagebox.showwarning("部分失败", "部分清除操作失败，请查看日志了解详情。")

    def _on_clean_error(self, error: str) -> None:
        self._set_busy(False)
        self.status_label.configure(text="清除出错", text_color=t.DANGER)
        self._log(f"\n错误: {error}")
        messagebox.showerror("错误", error)


def main() -> None:
    app = App()
    app.mainloop()
