# 本地中文小说创作环境

这是一个使用 Markdown、Git 和 Codex/Claude Code 等本地 Agent 协作的长篇小说项目模板。正文、设定和状态都保存在普通文本文件中，不依赖专有写作软件。

## 快速开始

1. 编辑 `config/project.yaml`，填写作品名称、类型、叙事视角和目标。
2. 完成 `bible/` 中的世界观与主要人物卡。
3. 在 `outline/master-outline.md` 写总纲，在 `outline/volumes/` 写卷纲。
4. 复制章纲模板，确认一章的目标后再开始正文。
5. 每章确认后，更新 `state/` 中的摘要、时间线、人物状态和伏笔。

建议先初始化版本控制：

```powershell
git init
git add .
git commit -m "初始化小说项目"
```

## 常用命令

检查目录、章节编号、元数据和状态引用：

```powershell
python scripts/novel_tools.py check
```

统计正文中文字符数：

```powershell
python scripts/novel_tools.py stats
```

创建下一章的章纲、正文和摘要文件：

```powershell
python scripts/novel_tools.py new-chapter --volume 1 --title "章节标题"
```

指定章节号：

```powershell
python scripts/novel_tools.py new-chapter --volume 1 --number 12 --title "雨夜来客"
```

## 推荐工作方式

- 构思阶段：让 Agent 提问、整理矛盾，不直接代写正文。
- 写章阶段：一次只处理一章或一个场景。
- 审校阶段：分别检查连续性、人物声音、节奏和语言，避免一次提示承担所有任务。
- 状态更新：只记录作者确认的正文事实。
- 每次重要修改后提交 Git，便于比较和回退。

## 目录说明

- `config/`：作品级规则和文风约束。
- `bible/`：世界观、人物、地点和术语等稳定设定。
- `outline/`：总纲、卷纲和章纲。
- `manuscript/`：正式正文。
- `state/`：当前剧情、人物状态、时间线、伏笔和摘要。
- `review/`：审校清单与审校报告。
- `templates/`：可复制的标准模板。
- `scripts/`：不依赖第三方包的本地辅助工具。
- `archive/`：废弃方案和旧稿；不要直接删除作者内容。

## 和 Agent 对话的示例

```text
阅读 AGENTS.md 和第一卷相关状态。检查第 3 章章纲是否与人物认知、时间线和未回收伏笔冲突，只给诊断和修改建议，不写正文。
```

```text
按照 chapter-003 的章纲起草第一个场景，控制在 1500 字以内。严格保持林舟的限知视角，不新增世界观规则。
```

```text
审校 chapter-003，只标出连续性、人物声音和 AI 套话问题。不要直接改稿。
```
