---
name: b2b-buyer-research
description: Research and qualify B2B buyer companies, procurement roles and public business contact routes; consolidate lead evidence or test advertising audience hypotheses across industries. Use for prospect research, CRM qualification and buyer-role targeting, not consumer profiling or unsolicited outreach.
---

# 企业买方研究与受众验证

把用户的产品和交易模式转成可验证企业、采购角色与联系入口，并明确证据支持到哪里。可处理设备、部件、OEM／ODM、批发、软件和服务；先识别交易差异，再选择资料源。中文或用户要求的语言交付。

## 先选当前工作

- 新买方研究：读[研究设计](references/01-research-design.md)、[发现与证据](references/02-discovery-evidence.md)、[采购角色](references/04-buying-committee.md)。
- CRM清洗或精选：读[联系人与数据](references/03-contacts-data.md)及[数据字典](references/08-data-contract.md)。
- 广告受众研究：在业务研究基础上读[平台验证](references/05-platform-testing.md)。
- 跨行业迁移：读[行业应用](references/07-cross-industry.md)，替换产品、数量、来源、角色和周期参数。
- 持续研究或交接：读[迭代与交付](references/06-iteration-handoff.md)。

## 执行准则

1. 从已有材料建立简报：交易对象、单位、买方模式、市场、规模门槛、人数口径、字段和允许的操作。缺少成交样本可继续公开研究；不要反复索取用户已说明没有的资料。
2. 企业先于联系人。用同一主体的目标产品、商业模式和外部采购路径判断企业资格；把当前需求、规模信号和具体订单量分别记证据。行业相关不能代替买方身份。
3. 角色按采购动作判断。读取实际职责中的采购对象、供应商动作、权限、事业部、地点和阶段。发起、引入、技术验收、批准、付款、补货各有用途，按本次目标选取。
4. 字段级溯源。姓名、岗位、电话、邮箱、品牌关系、供应商关系各自有来源。保持原值与规范值；不推邮箱、不借总机补个人电话、不从手机号推WhatsApp。
5. 表内行、独立企业、不同个人、独立联系路线、设备型号和平台账户分别计数。优先按电话／邮箱排查路线重复；同一路线可以被多人共用，不能据此自动合并人。
6. 联系人名单、广告信号和实际采购是不同成果。平台搜索必须证明候选类别、查询有效性与当前范围；无结果、未测和查询失败分开。
7. 维护前提。企业集合、地域、目标或交易单位变化时，重算依赖它的保留项和排除项。旧方案的阈值、职位与受众规模不能自动继承。
8. 交出可用数据与具体结论。数量不足按真实缺口交付，已有反证不能靠放宽评分恢复。用户另要求固定前N相对排序时，把弱项标清并分开严格候选。

## 状态与能力边界

研究、表格生成、格式校验、已保存、已发布、已匹配、已触达、已回复和已成交分别报告。公开来源可用于核商业事实，其广告用途依据另记。除非用户明确授权，不联系、不上传、不发布或改动其他账户对象。

工具不可用时完成独立工作，记录待核项。不要把认证失败、页面阻断、旧列表或缺失文件当阴性证据。不存在可靠替代时说明具体缺口。

## 资源

- `assets/project-brief.json`：可配置简报，所有数量与地域默认空。
- `assets/templates/`：企业、人员、联系方式、角色、证据、平台测试和决策表。
- `scripts/research_ops.py`：标准库建表、结构审计和OR／AND展开；不会联网或自动判定买家。

研究结束前用来源重核重要结论及计数，查看实际文件。脚本通过只证明它覆盖的结构要求；网页真实性、现在是否在职、是否愿意采购与广告效果仍需对应证据。
