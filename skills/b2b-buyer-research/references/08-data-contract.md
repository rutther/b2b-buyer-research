# 数据契约与脚本使用

所有CSV采用UTF-8，首行表头。空字符串表示未知，不等于0或否。ID由研究项目分配，不以姓名、电话号码或行号当永久ID。多证据引用用分号分隔，如 `E01;E02`。原始来源不改写，工作表可另建。

## 表之间的关系

`accounts` 是企业主体，`people` 是个人，`roles` 是已知岗位及动作（允许暂未找到姓名），`routes` 是联系路线。证据统一存在 `evidence`，决策与平台测试分别存表。

一家企业可以有多个角色与个人；一个号码可以被多人共用。`route_id` 标记一条“归属声明”，所以不同归属声明可以有相同规范号码。审计会提示共用，不自动合并人。不同法人关系用parent_id并附证据，不能用共同品牌名直接合并。

| 表 | 关键字段 | 含义 |
| --- | --- | --- |
| accounts | account_id, legal_name, brand, parent_id, country | 主体、品牌、母子关系、主体所在国家 |
| accounts | product_scope, business_model, transaction_unit | 产品、买方模式、单笔/项目/年度等交易单位 |
| accounts | fit_status, external_sourcing_status, demand_status | 品类商业匹配、外采链、需求证据分别判断 |
| accounts | quantity, quantity_unit, quantity_scope | 数量、单位和口径，如台/单笔、席位/年度；不能用营业额填 |
| accounts | evidence_ids, next_action | 引用及下一证据缺口 |
| people | person_id, account_id, name, original_title, function, stage, authority_status, work_country, evidence_ids | 人员身份、原职称、功能、采购阶段、职权和工作地 |
| roles | role_id, account_id, original_title, procurement_object, actions, stage, authority_status, evidence_ids | 不依赖姓名的角色研究，强调对象和动作 |
| routes | route_id, person_id, account_id, kind, value_raw, value_normalized | 路线归属声明、原始值和规范值 |
| routes | ownership, contact_status, checked_at, evidence_ids, use_basis_status | 归属、是否联系验证、日期、证据和用途依据 |
| evidence | evidence_id, entity_id, field, claim | 哪个实体的哪个字段，来源支持的具体主张 |
| evidence | source_url, source_date, checked_at, location, evidence_status, limits | 来源地址/相对文档路径、原日期、核查日期、页码/定位、证据状态与局限 |
| platform_tests | test_id, query, object_type, exact_label, object_id, query_status | 原查询、对象类别、准确结果、平台ID与查询状态 |
| platform_tests | positive_control, control_status, context, checked_at, evidence_ids | 对照、结果、账户/语言/地域范围、核查日期和截图依据 |
| decisions | decision_id, entity_id, decision, reason, depends_on, supersedes, checked_at, reopen_trigger, evidence_ids | 决策、依赖、替代的旧决策及复查触发条件 |

## 状态值

新增数据行时，状态字段必须显式填写以下枚举；未知用unknown、unverified或not_recorded等对应值，不能留空。其他非必需事实字段可留空。

- fit_status: `qualified` / `candidate` / `rejected` / `unknown`。qualified只表示达到该项目明示的企业门槛，非已成交。
- external_sourcing_status: `confirmed` / `signal` / `unknown` / `not_applicable`。
- demand_status: `current_need` / `scale_signal` / `historical` / `unknown`。current_need要有同主体demand_status字段证据及明确时间窗口；结构审计不能自行证明其仍有效。
- authority_status: `confirmed` / `signal` / `unknown`。
- ownership: `personal` / `shared` / `company` / `unknown`。
- contact_status: `public_only` / `dialed` / `replied` / `unverified`。是否WhatsApp需独立证据，不从手机号推断。
- kind: `email` / `phone` / `url`。不推测国家码；含分机的电话保留原文，规范时保留分机。
- use_basis_status: `not_recorded` / `documented` / `restricted`。documented仅说明存在用途记录，脚本不提供广告上传批准。
- evidence_status: `verified` / `historical` / `conflicting` / `unverified`。verified指研究者记录的证据核查状态，不等于脚本核实了网页。
- query_status: `exact_found` / `no_exact` / `pending` / `failed`。no_exact需成功阳性对照，且只是该时点／查询范围未返回。
- control_status: `pass` / `fail` / `not_run`。
- decision: `keep` / `hold` / `reject` / `reopen`。拒绝应说明前提，缺少证据一般hold，不自动reject。

## 可执行操作

```text
python skills/b2b-buyer-research/scripts/research_ops.py init --out work/example
python skills/b2b-buyer-research/scripts/research_ops.py audit --project work/example
python skills/b2b-buyer-research/scripts/research_ops.py logic --config examples/logic.json
```

init拒绝非空输出目录。audit只读取项目，输出JSON，0为结构未发现错误，1为结构错误，2为参数/读写失败。空项目会提示未开展研究，不会宣布完成。warning不阻止返回0，但仍需人/AI解释。审计不会改表、联网、猜测邮箱、合并人或生成分数。

结构审计范围：必需列、重复表头/ID、跨表引用、未知状态、联系方式规范一致性、共享路线、qualified/confirmed/current_need等强声明的同实体字段证据、数量单位、无效阴性查询及用途声明。它不判断企业是否真的达到门槛，也不计算合格买家总数。证据关联检查只能防止缺引用或明显串主体，不能替代阅读原文。

logic接受 `{"layers":[["A","B"],["X","Y"]]}`，返回4条组合：A AND X、A AND Y、B AND X、B AND Y。不预测受众大小，不证明平台按硬条件执行。空层/重复词会报错，超过10,000条路径拒绝展开以免误用。

## 原有CRM与Meta模板

已有固定21列或其他CRM格式时，保持原表，另用ID映射到本契约，不强迫改列。Meta的重复email/phone表头必须按列位置解析，不能直接用字典吞掉重复列。通用脚本read_matrix保留表头与位置，但工作契约本身要求唯一列名。

电话号码、邮编、ID和邮箱为文本。工作簿保存文本类型；CSV直接双击可能被表格软件自动转换，导入时指定文本。以`= + - @`开头的任意外来文本还需评估公式注入，不能为防注入而不可逆改掉原始证据。

value如是真实交易价值，要记录币种、周期和定义；相对排序分另列，不伪装金额或生命周期价值。广告匹配文件即使格式通过，公开来源也不自动产生用途许可。
