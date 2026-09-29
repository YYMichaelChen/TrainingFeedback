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

## 用户自行安装与测试

请使用普通用户账户、隔离的 `%LOCALAPPDATA%` 配置和纯合成数据目录，手动安装并操作上述 SHA-256 对应的安装包。每项完成后勾选，并填写测试账户、实际路径、输入、观察结果及证据位置。**勾选只表示已执行；只有记录了实际结果，才能将状态改为「通过」或「失败」。**未执行的项目保留 `not run`。

- [ ] **安装与文件核对**：安装成功；安装后的文件与完整载荷清单一致；安装前已关闭的隔离数据目录和定位文件保持不变。状态：`not run`；实际记录：待填写。
- [ ] **首次启动取消**：取消选择数据目录后，没有创建定位文件或新子目录。状态：`not run`；实际记录：待填写。
- [ ] **创建表单**：重定向后的“文档”目录建议正确；父目录、子目录名及完整路径预览一致；无效名称不能确认；确认前不写入文件。状态：`not run`；实际记录：待填写。
- [ ] **子目录状态**：不存在和已存在但为空的子目录可创建；已有有效根提示明确打开；占用、不完整、未来版本及过期根均原样拒绝。状态：`not run`；实际记录：待填写。
- [ ] **新根内容**：使用含中文或空格的名称创建；完整内置动作目录和图片可见；没有凭空生成个人审核、计划或训练事实。状态：`not run`；实际记录：待填写。
- [ ] **设置页与直接打开**：从设置页创建新根；直接打开受支持的已有根和备份副本；备份目标仍按完整根目录处理。状态：`not run`；实际记录：待填写。
- [ ] **重启与兼容性**：隔离定位文件在重启后生效；0.7.5／0.7.6 的 schema 23 根可重新打开，已提交的清理日志可继续完成；schema 22 根只读拒绝且原始字节不变。状态：`not run`；实际记录：待填写。

只要必需项目仍为 `not run`，本地安装验收就未完成。公开发布验收、外部内容审核、W4 和个人使用准备各有独立门槛，本候选尚无这些结果。
