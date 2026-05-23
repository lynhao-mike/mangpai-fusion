# theory/ · 4 派结构化规律库

本目录存放 4 派的**结构化规律**，是分析引擎的直接调用对象。

```
theory/
├── SCHEMA.md              规律统一 schema 定义（必读）
├── gao/*.yaml             高派结构化规律（M2 阶段产出）
├── duan/*.yaml            段派结构化规律（M2 阶段产出）
├── yang/*.yaml            杨派结构化规律（M3 阶段产出）
├── ren/*.yaml             任派结构化规律（M3 阶段产出）
└── raw/                   原始抽取记录（追溯链）
    ├── gao/
    │   ├── extracted/     高派候选规律抽取记录
    │   └── promoted/      高派已晋级模块文件
    ├── duan/              段派理论抽取（D01-D29）
    │   └── promoted/      段派已晋级模块
    ├── yang/              杨派理论抽取（Y01-Y29）
    │   └── promoted/      杨派已晋级模块
    ├── ren/               任派理论抽取（R01-R30）
    │   └── promoted/      任派已晋级模块
    ├── _legacy-shared-rules/    gufamangpai 已有的三派共识参考
    └── _legacy-protocol-ref/    gufamangpai 已有的引擎参考
```

---

## 工作流

```
sources/{school}/                ← 原始文档（不变）
        ↓
theory/raw/{school}/             ← 已抽取的散文/半结构化（已迁入）
        ↓ 转写
theory/{school}/*.yaml           ← 标准 schema 结构化规律（M2/M3 产出）
        ↓ 跨派对照
mapping/{consensus,complementary,exclusive,conflicts}.md
                                 ← 跨派关系矩阵（M4 产出）
```

每条规律必填字段见 [`SCHEMA.md`](./SCHEMA.md)。
