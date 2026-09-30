# v0.8.0 实施进度

开发工作区记录；不是安装候选或客户端验收。需求由 [设计](design.md) 和
[产品规范](../../development-plan.md) 负责。当前运行身份为 0.8.0 / schema23 /
catalog070-illustrated-3 / contract3；应用版本已集成，其它身份不变。

## T-005 安装路径与程序所有权（2026-09-30）

Inno 明确显示目录页、保留默认位置、预填同 AppId 的原目录，ready 页面展示
最终路径。通过完整临时 payload 的内部 CLI 在目录页、准备安装和实际写入前
执行检查；CLI 在 Qt 入口之前分派。没有真实根或默认 locator 的开发执行。

`data/installation.py` 校验本地绝对路径、Windows 名称、危险范围、locator
目录、已知根与目标祖先 marker。拒绝重解析点、硬链接、无关文件/空子目录和
损坏的程序 receipt；只读探测不创建程序目录，不打开任何用户数据库。
Windows 名称规则移到纯 domain 模块，原 new_root 导入接口和原文行为保留。

构建生成 `.training-feedback-program.json`，安装后记录 exact payload hash
和确切 Inno uninstaller 的 `.training-feedback-install.json`。原 `_internal`
通配递归删除及历史快捷方式猜测清理已移除；过期 payload 文件只在清单和 hash
重新核验后，通过已绑定 Windows 对象句柄删除。未知文件导致拒绝而不是清理。

更换目录时先检查原安装 receipt 和精确卸载器，确认后仅卸载原程序，并传
`/KEEPDATA`；静默 `/DIR` 走相同安全检查。旧程序删除失败或 exe 仍存在则停止。
旧位置卸载成功、后续新安装失败时，明确报告需重装程序，数据根/locator 保留。
取消发生在程序卸载前时不改 locator/root。没有新 receipt 的旧开发安装不会被
猜测为归属已知的安装，提示先显式卸载程序；这不是旧版本兼容保证。
快捷方式由同 AppId 的 Inno 安装/卸载记录管理，不删除猜测的旧入口。

验证：T-005 dev scope 24 unique cases，通过（首次 23 passed / 1 failed，为
测试错误消息断言；修复后该用例通过）。句柄后端接入后受影响清理 2 cases
再通过，未新增 scope。实际 junction/硬链接仅在 pytest 临时合成目录创建。
Inno 6.7.3 对合成假 exe/dll payload 编译通过，产物仅为脚本编译样本，
没有运行安装器；不能冒充可安装候选。Ruff/diff/docs 检查随每批更新。

客户端和安装路径/快捷方式/迁移的手动验收均 **not run**。程序目录权限和
Inno 与 helper 的运行期协作仍需精确候选手测，静态编译不替代该证据。

## T-006 单一当前根的可选删除

接口与失败要求见 [卸载助手设计](uninstall-design.md)。受控内部 CLI 使用固定
本用户 locator，最多操作一个根；无任意根删除命令。普通/静默卸载与 `/KEEPDATA`
保留数据，勾选与二次确认仅绑定删除 offer，真正删除在 Inno 最终确认后的
`usUninstall` 阶段、程序 payload 删除前执行。取消与确认后拒绝保留数据。

`BoundTree` 持有祖先、根、每个子目录和文件的 Windows 句柄，拒绝重解析点、
硬链接、其它所有者、只读与冲突打开句柄。目录句柄也拒绝其它写句柄，防止清单
读取期间将空目录转换为连接；创建子文件仍可完成。最终安全复查在原 release
scope 内复核。文件独占绑定，删除用
`SetFileInformationByHandle`，不递归删除任何 locator 路径字符串。预检读取
句柄绑定的 marker/config 和 SQLite 字节，在内存中检查当前 schema、integrity
与外键，不运行根上的迁移、恢复或写入。先验证本应用 marker 再枚举数据库。

确认 token 绑定卷/file ID、文件 hash、清单和 locator；修改/换根/新增文件后拒绝。
固定本用户外部恢复记录在删除前写入、每项记录意图/完成状态；根内中断标记
使普通启动只读拒绝部分清理目录。锁文件与中断标记保留至最后阶段。恢复仅
接受同一剩余对象身份，并再确认；根外备份、历史根不发现也不删除。
根已删而 locator 或记录清理失败的状态分别报告、分别可重试，不报假完成。

T-006 dev scope 28 unique cases passed（26 清理场景与 2 当前根安全回归）；包括实际 junction/hardlink/只读拒绝、
使用中根、当前/未来格式、取消、换根/locator、各删除阶段中断、真实子进程
退出后的句柄释放与同根恢复，以及 CLI probe/确认接口。最初 future-schema
fixture 未关闭 SQLite 连接，被正确拒绝为 busy；修复 fixture 后该 case 通过。
Inno 合成 payload 编译通过，未操作客户端或安装器。新增中断拒绝提示已有中文映射。

安装/卸载、长路径、中文路径、权限与可用性仍须精确候选的开发者手动验收，
均 **not run**。代码测试不代表完整安装验收、公开发布、内容审批、W4 或个人转换。
