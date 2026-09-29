# 0.7.7 Local Candidate And Installed Acceptance

## Candidate identity

- Source commit: `831f7edf2f80a062f5919223b10cada4037f577b`; clean at build.
- Application `0.7.7`, schema `23`, catalog `070-illustrated-3`, plan/evidence
  wire contracts v3. Python `3.12.14` AMD64, PySide6 `6.11.2`, PyInstaller
  `6.22.2`, Inno Setup `6.7.3` on Windows 11.
- Directory payload: `dist/TrainingFeedback/`; 295 files. The complete file
  inventory, sizes and SHA-256 values match the adjacent build manifest; no
  missing, extra or mismatched files. The bundled catalog verified with 36
  illustrations. `schema23.sql` and `plan-v3.schema.json` are present;
  retired `schema22.sql` is absent. The build script found no locator or user
  database in the payload.
- Build manifest SHA-256:
  `9d7deb4651547ecf217618c3c914a4e2564d179935e633f47a2b500fb990271b`.
- EXE SHA-256:
  `9da31103b7e103a8bca18506e60cca1f227bddfd72627b5cd3e8cc18bf5a3b08`.
- Setup: `dist/installer/TrainingFeedback-0.7.7-Setup.exe`; SHA-256
  `b3b8573274bb95b0b71056a0504dd3e5a5de5493a21f58484906e425ae093279`.
  Its installer manifest records the same hash and includes the payload build
  manifest. Installer manifest SHA-256:
  `bc34c6958d91dd04ca53f9972ee1bd0eaeff72daa4f1868bc61295621bc3e512`.
- Authenticode: `NotSigned` (local candidate; no public release claim).

An earlier clean build from commit `154fce4` passed static manifest inspection,
then was superseded before any installed client check by the error-handling
correction in `831f7ed`. Its checks do not certify this candidate.

## 用户实际操作记录

- [x] **安装并打开应用**：用户于 2026-09-29 报告“我已直接安装打开了”。这是用户对实际操作的报告；所用安装包哈希、账户、数据目录及界面观察尚未记录，不能据此确认上述候选已通过完整安装验收。

用户还报告已在安装后的应用中创建并看到新目录，并于 2026-09-29 确认以下三项实际操作均符合预期。以下只记录 0.7.7 新功能的直接界面观察；不要求重新安装、核对文件散列或构造旧版数据库。

- [x] **新建并看到目录**：用户报告“已创建并看到新目录”。这是已执行的观察；具体父目录、名称、候选身份及完整路径尚未记录。
- [x] **路径预览**：用户报告显示的完整路径与实际新建目录一致；具体路径未提供。结果：用户报告符合预期。
- [x] **设置页创建**：用户报告设置页的父目录、名称和路径预览符合预期；具体路径未提供。结果：用户报告符合预期。
- [x] **打开已有目录**：用户报告直接选择已有根可打开，未追加子目录；具体根身份未提供。结果：用户报告符合预期。

## 本地验收范围

用户所述的 0.7.7 直接界面操作已验证完毕。构建脚本已核对打包载荷；所装文件的确切哈希、安装后的文件一致性、隔离数据根、取消创建、重启保留以及旧版根兼容性尚无手动结果，均为 `not run`。因此不能宣称完整的本地安装验收通过。公开发布验收、外部内容审核、W4 和个人使用准备各有独立门槛，本候选尚无这些结果。

## 2026-09-29 部分验收收尾

用户明确批准 0.7.7 按部分验收结果收尾并继续开发。上述五项已勾选的界面操作为用户报告的实际观察；其余项目保持 `not run`，不计作通过。此收尾只表示 0.7.7 开发版本完成，不表示该候选通过完整本地安装验收。
