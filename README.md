# Xenium Cancer Data Radar

一个可运行的 Python 3.11 元数据雷达：发现公开的人类癌症 Xenium 数据，优先标记 Cell、Nature、Science 系列论文，并独立检索单细胞、空间组学和病理 foundation model。系统只保存文件清单和 URL，**绝不下载大型数据文件**。

## 安装

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # 可选；请勿提交密钥
pytest
```

所有运行配置位于 `config/settings.yaml`，癌种映射位于 `config/cancer_ontology.yaml`。默认 SQLite 为 `data/radar.sqlite3`，导出目录为 `data/exports/`。

## 运行

```bash
python -m xenium_radar search-literature
python -m xenium_radar search-repositories
python -m xenium_radar resolve-accessions
python -m xenium_radar validate-downloads
python -m xenium_radar update-all
python -m xenium_radar export
streamlit run app.py
```

网页包含 Overview、New datasets、Dataset explorer、Cancer type summary、Foundation model papers、Manual review queue、Failed URL checks 和 Search configuration，并可筛选与下载当前 CSV；文件下载链接不会被代理。

## 架构与数据源

`BaseSource.search()` 统一返回 Pydantic `DatasetRecord`。独立适配器覆盖 Europe PMC、Crossref、PubMed、GEO/GDS、GEO FTP 清单、BioStudies、Zenodo、Figshare、OpenAlex、bioRxiv、medRxiv、arXiv、Hugging Face 和 10x Genomics。第一阶段核心是 Europe PMC、GEO 和 BioStudies；其余适配器提供可配置的 API MVP，站点发生 schema 变化时记录错误并继续其他来源。

网络层统一设置 User-Agent、timeout、Retry 和指数退避。下载验证优先 HEAD，服务不支持时仅 Range GET 一个字节。部分仓库会返回鉴权页；系统记录状态、Content-Length、Content-Type、Range、Last-Modified、登录要求及公开性。

## 数据字段

记录包括论文 DOI/PMID/PMCID、期刊/ISSN/publisher/container、日期和 URL；数据 accession、仓库、文件清单/大小/格式/可下载性；物种、癌种原名和标准名、组织、患者/样本/切片/细胞/基因 panel；Xenium 角色、配对模态；foundation model 名称、任务、训练规模、代码/权重/训练数据公开性；证据、置信度、人工复核状态，以及 `first_seen_at`、`last_checked_at`、`source_updated_at`。SQLite upsert 保留首次发现时间。去重依次利用 DOI、PMID、accession、规范化标题；key 保留 accession，因此同一论文的多个数据集不会错误合并。

## 配置扩展

- **新期刊**：向 `config/settings.yaml` 的 `journals` 添加规范名称；适配器仍保存 ISSN、publisher 和 container title，白名单不是唯一证据。
- **新癌种**：向 `config/cancer_ontology.yaml` 添加 `原始名称: 标准名称`，并按需将检索词加入 `keywords.cancer`。
- **新仓库**：在 `src/xenium_radar/sources/` 新建继承 `BaseSource` 的类，实现 `search()`，注册到 `pipeline.py`，并在 YAML `sources` 中添加开关。复用 `HttpClient`，不要直接发出无 timeout 的请求。

## GitHub Actions

`.github/workflows/daily.yml` 每天 UTC 03:17 或手工触发，固定 Python 3.11，安装依赖、运行离线测试、更新并导出结果。若需要 NCBI 配额，在仓库 Settings → Secrets and variables → Actions 创建 `NCBI_API_KEY`。工作流只提交 `data/exports/*`；按机构策略也可改为 artifact 或外部对象存储。

## API 使用限制

请将 YAML 中的 User-Agent 邮箱改成真实维护者地址，并遵守各服务速率限制和许可。Crossref 推荐提供联系邮箱，NCBI 无 key 通常限约 3 请求/秒；Zenodo、Figshare、OpenAlex、Hugging Face 与预印本 API 可能分页、限流或改变 schema；10x 页面可能不是稳定公共 API。429/5xx 会自动重试，但本工具不会绕过登录、许可或受控访问。

## 测试与内置 fixture

测试全部 mock 网络，覆盖 GSE、S-BIAD、Data Availability、primary/validation、人与小鼠、癌症与正常、大小解析、DOI 去重、超时/重试和 GEO 文件清单。`tests/fixtures/integration_records.yaml` 含 GSE311609、GSE300147、S-BIAD2146，仅作为回归 fixture，不会写入正式结果。

## 已知限制

元数据文本经常不完整，患者数、Xenium 角色和公开性可能需要人工复核；受控数据不会变为公开下载。全文及补充材料解析受版权、robots、登录和 API 能力限制。通用适配器只实现公开元数据的最小共同字段，复杂分页、10x 页面变化、Hugging Face dataset ID/Zenodo/Figshare DOI 的深层解析需要按服务迭代。关键词分类是可解释启发式而非医学结论，网页的 Failed URL 页面在 MVP 中展示存储记录而非后台任务日志。
