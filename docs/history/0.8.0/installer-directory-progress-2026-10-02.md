# 安装目录检查的等待反馈与重复检查修复

开发者在408df076候选的安装目录页点击Next后报告卡顿几秒。首次辅助检查
同步解压完整payload，同路径重装还会在旧程序完整验证之后再次完整验证同一
目标，期间目录页没有等待反馈。未测量精确耗时，不能把代码路径计数当秒数。

`packaging/training_feedback.iss` 现在使用
[Inno标准等待进度页](https://jrsoftware.org/ishelp/topic_isxfunc_createoutputmarqueeprogresspage.htm)：
点击Next进入“正在检查安装目录”，显示当前路径与“请稍候”，检查后在finally
隐藏进度页，回到原页面再显示错误或继续。静默安装不显示该页。
同一次Next中，刚完成的旧程序及卸载器检查已覆盖完全相同的目标时，省略
额外的目标validate调用。选择不同路径仍检查重叠/边界/归属，真正安装前
PrepareToInstall和prepare阶段仍保留原检查；没有跨操作缓存、跳过校验或触碰数据。
开始/结束记录写入Inno日志，后续开发者可提供日志作实际等待证据。

同一release-0.8.0 minor范围的26个既有安装案例通过/0.52s，仍100/100 unique；
合成payload Inno6.7.3编译通过/1.140s。这些不认证窗口显示、进度动画、响应性、
实际耗时或完整新候选安装；客户端检查尚未运行，等待干净源码完整构建。
应用0.8.0/schema23/catalog070-illustrated-3/contract3均不变，Python程序行为及
数据策略不变。旧408df076候选的手动通过只属于旧包，新包需检查受影响目录页。
构建前Ruff、50份Markdown文档检查及git diff --check均通过。新目录页逻辑未
执行自动客户端操作，进度显示与同路径去重的安装调用仍需开发者手动复测。
