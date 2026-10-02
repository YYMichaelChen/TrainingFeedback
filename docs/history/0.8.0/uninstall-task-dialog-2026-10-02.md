# 2026-10-02 第二次尺寸失败后替换卸载对话框

[第二次截图](evidence/uninstall-dialog-still-oversized-2026-10-02.png) 证明尺寸修复
未生效，并且底部控件不可见。只增加边框、居中和尺寸约束不足以解决本机现象，
不能归因于开发者没有重开窗口或继续要求同一个窗口验收。

移除CreateCustomForm、TNewMemo、手动控件定位和尺寸约束，卸载选择使用
[Inno TaskDialogMsgBox接口](https://jrsoftware.org/ishelp/topic_isxfunc_taskdialogmsgbox.htm)。
其维护的对话框布局处理文字与按钮。第一项仅卸载并保留数据，删除为明确独立选择；
预检拒绝时不提供删除入口，保留中文原因与取消按钮。窗口实际显示仍待新包手动检查，
不声称仅凭编译已修复本机显示。

选择删除后仍单独确认确切路径，使用MsgBox的默认“否”。拒绝直接取消卸载，
关闭、Esc、取消或对话框返回0也不删除。不改变只允许当前用户的一个当前根、
句柄绑定和静默保留边界，不修改现有A/B或ACL。对应设计文件同步由复选框改为
默认未选择删除的按钮；产品默认保留与双确认语义不变。

核对了 [6.7.3官方实现](https://github.com/jrsoftware/issrc/blob/is-6_7_3/Projects/Src/Shared.TaskDialogFunc.pas)：
TaskDialogMsgBox只支持列出的按钮类型，不支持附加MB_DEFBUTTON标志，不能向它传
该标志。默认安全语义由首项保留和删除的二次默认“否”保证。TaskDialog可能使用
系统或Inno主题实现，不能承诺它总是直接调用原生Windows对话框。

应用0.8.0/schema23/catalog070-illustrated-3/contract3不变。只改交互层，不增加
schema或外部格式。原候选结果只认证各自构建，未建立正式/公开发布或个人使用资格。

Inno6.7.3完整编译通过。原release-0.8.0 minor scope的3项既有取消/未确认保留/
异用户归属拒绝测试复测通过（0.17s），累计仍100/100 unique，未受影响后端结果复用。
没有执行客户端、安装器或卸载器做自动验收。新包窗口显示与按钮操作仍not run。
