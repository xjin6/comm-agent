# Project Context

> Fill in this file to describe your study.
> This file is excluded from git — your research content stays local.

## Study Overview

**Title:** 
**Institution:** 
**Data file:** `your-project/data/`

Brief description of the study (topic, population, method):

---

## Variables

Source table: `article_detail` (2109 rows, 32 columns) from `cssci805969.sql`

| Column Index | Field Name | Label (中文) | Description | Fill Rate |
|---|---|---|---|---|
| 0 | id | 主键 | Auto-increment primary key | 100% |
| 1 | flag | 标志位 | Flag field, all 0 | 100% |
| 2 | cite_count_cssci | CSSCI被引次数 | Times cited within CSSCI | 14% |
| 3 | download_count | 下载次数 | Download count | 100% |
| 4 | view_count | 浏览量 | Page view count | 100% |
| 5 | discipline_code | 学科代码 | Discipline code (e.g. 0401, 020101) | 60% |
| 6 | is_deleted | 删除标志 | Deletion flag, all 0 | 100% |
| 7 | source_type | 来源类型 | Source type (1=CSSCI core, 3=extended) | 100% |
| 8 | journal_name | 期刊名称 | Journal name | 100% |
| 9 | issue | 期号 | Issue number | 7% |
| 10 | volume_or_type | 卷号/类型 | Volume or type code | 100% |
| 11 | year | 发表年份 | Publication year | 100% |
| 12 | clc_code | 中图分类号 | Chinese Library Classification code | 13% |
| 13 | title_zh | 中文标题 | Article title in Chinese | 100% |
| 14 | keywords_zh | 中文关键词 | Keywords in Chinese (aaa词aaa; format) | 100% |
| 15 | (empty) | 空列 | No data | 0% |
| 16 | pages | 页码 | Page range (e.g. 23-26) | 100% |
| 17 | article_id | 文章编号 | CSSCI unique article identifier | 100% |
| 18 | subject_code | 学科分类代码 | Subject classification code (e.g. F830.9) | 100% |
| 19 | journal_code | 期刊代码 | Journal identifier code | 100% |
| 20 | fund_info | 基金资助信息 | Funding/grant information | 7% |
| 21 | (empty) | 空列 | No data | 0% |
| 22 | author_position | 作者顺序 | Author order info (e.g. 4/8) | 5% |
| 23 | authors | 作者姓名 | Author names (aaa姓名aaa format) | 100% |
| 24 | institutions | 作者机构 | Author institutions (aaa机构aaa; format) | 100% |
| 25 | title_pinyin | 标题拼音 | Article title in Pinyin romanization | 100% |
| 26 | title_en | 英文标题 | Article title in English | 68% |
| 27 | author_postal_codes | 作者邮编 | Author postal codes | 100% |
| 28 | category_code | 类别代码 | Category code (e.g. 040, 010) | 100% |
| 29 | journal_year_code | 期刊年份码 | Journal + year combined code | 100% |
| 30 | (empty) | 空列 | No data | 0% |
| 31 | md5 | MD5哈希 | Record MD5 hash for deduplication | 100% |

Secondary table: `article_citation` (citation relationships)
| Column | Field Name | Description |
|---|---|---|
| 0 | id | Auto-increment id |
| 1 | article_id | Citing article CSSCI ID |
| 2 | cited_title | Title of cited work |
| 3 | pub_year | Publication year of citing article |
| 4 | cite_year | Publication year of cited work |

---

## Constructs / Scales

| Construct | Variables | Description |
|-----------|-----------|-------------|
|  |  |  |

---

## Research Questions

- RQ1: 
- RQ2: 

## Hypotheses

- H1: 
- H2: 

---

## Data Notes

- Sample size: N = 
- Reverse-coded items:
- Attention check items:
