# RDP 连接记录清除工具

一键清除 Windows 远程桌面（mstsc.exe）的连接历史记录。

**当前版本：v1.0.0**

## 下载

无需安装 Python，直接下载 exe 使用：

[下载 RDP_Cleaner.exe (v1.0.0)](https://github.com/datuzi-vip/rdp_cleaner/releases/download/v1.0.0/RDP_Cleaner.exe)

更多版本见 [Releases](https://github.com/datuzi-vip/rdp_cleaner/releases)。

## 功能

- 清除注册表 MRU 最近连接列表
- 清除注册表 Servers 历史主机及用户名提示
- 删除 `Documents\Default.rdp` 配置文件
- 清除任务栏 / 开始菜单 Jump List 中的 RDP 记录
- 可选：清除凭据管理器中的 TERMSRV 保存密码

## 环境要求

- Windows 10 / 11
- Python 3.11+

## 安装与运行

```powershell
git clone https://github.com/datuzi-vip/rdp_cleaner.git
cd rdp_cleaner
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## 打包为 exe

```powershell
pip install pyinstaller
pyinstaller build.spec
```

生成的可执行文件位于 `dist\RDP_Cleaner.exe`，双击即可运行，无需安装 Python。

## 使用说明

1. 启动程序后会自动扫描并显示当前 RDP 连接记录
2. 勾选需要清除的项目（凭据清除默认关闭）
3. 点击「一键清除」并确认

清除完成后，重新打开远程桌面连接（mstsc）即可看到 Computer 框已清空。若 Jump List 仍显示旧记录，可重启资源管理器或注销重新登录。

## 注意事项

- 本工具仅修改当前用户（HKCU）下的 RDP 相关数据，通常无需管理员权限
- 清除凭据将删除已保存的 RDP 密码，下次连接需重新输入
- 清除前请关闭正在运行的远程桌面连接窗口
