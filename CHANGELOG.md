# Changelog

## [1.0.0] - 2026-07-05

### Added

- 一键清除 Windows RDP（mstsc）连接历史记录
- 清除注册表 MRU 最近连接与 Servers 历史主机
- 删除 `Default.rdp` 配置文件
- 清除任务栏 / 开始菜单 Jump List 记录
- 可选清除 TERMSRV 保存凭据
- 现代化图形界面：统计卡片、选项徽章、自动扫描预览
- 支持 PyInstaller 打包为独立 exe

### Notes

- 仅修改当前用户（HKCU）数据，通常无需管理员权限
- 清除前会自动尝试关闭 mstsc.exe 进程
