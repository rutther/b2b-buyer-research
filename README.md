# 跨行业 B2B 买方研究方法包

从“这家公司可能相关”走到“谁负责采购、依据是什么、应通过什么渠道接近”。适用于设备、消费品OEM／ODM、工业项目、软件和服务采购研究，也支持把买方证据转成广告受众假设。

这套方法来自一项长期出口客资与Meta定位研究。它保留实际遇到的身份混淆、同号多人、采购方向误判、旧网页、平台搜索假阴性和两层组合误入等经验，去掉特定产品、国家、订单门槛及账户依赖。它没有声称已在所有行业实测获客效果。

## 开始使用

**支持Skill的工具：** 把完整的 `skills/b2b-buyer-research/` 文件夹放进该工具支持的技能目录。使用Codex时可放入当前项目的 `.agents/skills/`，或你配置的全局技能目录。保留目录内的 references、assets 和 scripts。实际加载规则以该工具版本为准。

**能读文件、没有Skill机制的工具：** 上传本包，告诉它先读 [START_HERE.md](START_HERE.md)，再按任务读取对应方法。不要只上传入口文件。

**只能上传单个文档：** 使用 `METHOD_ALL_IN_ONE.md`。它包含全部方法、数据字典和跨行业案例；可执行脚本仍需完整包。

可直接这样提需求：

> 请使用本包的方法研究我们的潜在企业买家。产品和交易模式是……，目标市场是……，规模门槛是……。先读取已有资料，输出企业、采购角色、联系方式归属和逐字段证据；缺失信息留空，报告真实缺口。涉及广告时另做平台信号验证。请持续维护当前状态、证据台账和决策变更记录。

缺少已成交客户样本不妨碍启动。工具应从官方产品、采购制度、渠道、型号文件和岗位职责建立可验证假设。

## 内容

| 文件 | 作用 |
| --- | --- |
| [START_HERE.md](START_HERE.md) | 按任务选择入口，说明不同工具如何接续 |
| [Skill](skills/b2b-buyer-research/SKILL.md) | 给AI读取的执行入口 |
| [研究设计](skills/b2b-buyer-research/references/01-research-design.md) | 产品、交易单位、买方模式、地区与规模门槛 |
| [证据研究](skills/b2b-buyer-research/references/02-discovery-evidence.md) | 搜索路径、文件取证、时间、关系连接和反证 |
| [联系人与数据](skills/b2b-buyer-research/references/03-contacts-data.md) | 实体归一、归属、去重、排序、名单用途 |
| [采购角色](skills/b2b-buyer-research/references/04-buying-committee.md) | 谁发起、谁选供应商、谁验收、谁批准 |
| [广告平台验证](skills/b2b-buyer-research/references/05-platform-testing.md) | 搜索有效性、准确对象、组合逻辑和交付边界 |
| [迭代与交付](skills/b2b-buyer-research/references/06-iteration-handoff.md) | 断点、决策更新、研究停止条件和成果验收 |
| [跨行业应用](skills/b2b-buyer-research/references/07-cross-industry.md) | 五种行业的完整合成案例与反例 |
| [数据字典](skills/b2b-buyer-research/references/08-data-contract.md) | CSV字段、状态及脚本约束 |
| [来源与泛化](PROVENANCE.md) | 从哪些实际经验提炼，以及哪些规则不能照搬 |
| [验证范围](VALIDATION.md) | 已执行的检查、仍未证明的事项 |

## 可选脚本

Python 3.10以上，标准库，无需密钥、联网、MCP或安装第三方包。从本仓库根目录运行：

```text
python skills/b2b-buyer-research/scripts/research_ops.py init --out work/new-project
python skills/b2b-buyer-research/scripts/research_ops.py audit --project work/new-project
python -m unittest discover -s tests -v
```

`init`只建立空表和研究简报，不生成客户。`audit`检查数据关系和声明所需的证据引用，不判断网页真假、不联系任何人，也不会自动合并姓名或上传名单。

## GitHub发布

只把这个目录作为仓库根目录上传。另交的私人成果包含真实名单和原研究记录，不属于本仓库。`.gitignore`帮助避免把work、原始数据和本地配置提交，但不能代替发布前查看暂存文件。

本包没有替你选择开源许可证。公开仓库与授予他人复用权是两项选择；选定许可证后再添加LICENSE。引用的官方页面只保留链接和方法说明，不附教材、个人名单、账户ID或抓取数据库。
