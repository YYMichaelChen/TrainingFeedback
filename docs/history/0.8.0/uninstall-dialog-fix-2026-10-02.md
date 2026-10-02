# 2026-10-02 卸载窗口与数据归属提示

## 开发者结果与边界

开发者在路径修复候选的程序乙运行卸载器，提供
[卸载窗口截图](evidence/uninstall-dialog-2026-10-02.png)。窗口异常铺满工作区，
控件集中在左上角，使用英文说明，删除选项不可用，原因是
`Selected data does not belong to the current user.`。显示与说明检查记为失败。

退出后的程序EXE为False、合成B和目录记录为True。这证明程序已卸载，B与目录
记录仍存在；不证明取消卸载通过，也不证明保留文件内容完整或重装后可重新打开。
直接取消、拒绝永久删除确认的操作没有结果，仍not run。

agent仅只读检查明确合成路径的Windows ACL：A、B和
`E:\TrainingFeedback-080-PathFix\测试配置\TrainingFeedback\locator.json` 的所有者
均为 `BUILTIN\Administrators`，当前执行账号所有者是个人用户SID，二者不一致。
没有读取locator内容、训练数据库或修改ACL。无法仅据此断言开发者PowerShell
是否提权；该组所有权可能与创建环境有关。此拒绝符合现有
[归属规则](../../releases/0.8.0/uninstall-design.md)，不是放宽删除边界的理由。

## 修复

自定义卸载对话框明确设置普通对话框边框、仅关闭按钮、居中与固定尺寸限制，
保留字体/DPI缩放，禁止WizardSizePercent额外放大，控件按实际客户区布局。
截图的具体原生窗口状态成因尚未通过手动复现定位；布局修复仍需实际新包检查。
Inno的 [CreateCustomForm](https://jrsoftware.org/ishelp/topic_isxfunc_createcustomform.htm)
和 [支持属性](https://jrsoftware.org/ishelp/topic_scriptclasses.htm) 是API依据；
[6.7.3源码](https://github.com/jrsoftware/issrc/blob/is-6_7_3/Projects/Src/Setup.ScriptFunc.pas)
本身已设bsDialog，不能把截图直接归因于API默认无边框。

标题、主要说明、选项、按钮与永久删除提示改为中文。拒绝归属时解释Windows
所有者可能为管理员组，明确不取得所有权、不改权限；继续按钮明确写“仅卸载程序”，
说明“取消”不会卸载，回车默认选择取消。仍保留默认不删除、两次确认、当前根和句柄绑定边界。

## 代码级验证

原release-0.8.0 minor scope的既有取消、CLI未确认保留、异用户拒绝三项复测
通过（3 passed/0.35s），累计仍100/100 unique，无新scope或新case。
其它未受影响后端结果复用，未重跑全部100项。Inno6.7.3完整编译通过，
文档检查通过39个Markdown，diff检查通过。没有启动客户端或卸载器；新窗口、
中文说明、默认取消和安装后行为仍not run。

应用0.8.0/schema23/catalog070-illustrated-3/contract3不变，无外部格式变更。
原路径修复候选的所有手动结果仍只认证其旧精确构建；新候选需独立记录身份。
旧包另存本地`.tmp/candidates/2026-10-02-path-fix/`，不删除现有合成A/B或其配置。
不得把此问题修复或本地候选当作正式/公开发布、个人使用或W4通过。
