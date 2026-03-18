# Git 分支管理策略

**量化交易实验室项目**  
**版本**: 1.0  
**创建时间**: 2026-03-18

---

## 🌿 分支结构

```
main (生产分支)
  ↖
   develop (开发主分支) ⭐ 当前默认分支
    ↖
     feature/* (功能分支)
     bugfix/* (修复分支)
     hotfix/* (紧急修复)
     release/* (发布分支)
```

---

## 📋 分支说明

### main 分支
- **用途**: 生产环境代码，稳定版本
- **保护**: 仅允许通过 Pull Request 合并
- **标签**: 每个版本打 tag (v0.1.0, v0.2.0, ...)
- **部署**: 自动部署到生产环境

### develop 分支 ⭐
- **用途**: 日常开发集成分支
- **保护**: 需要 Code Review
- **来源**: 从 main 分支创建
- **合并**: 功能分支合并到此分支

### feature/* 分支
- **用途**: 新功能开发
- **命名**: `feature/<功能名称>`
- **来源**: develop 分支
- **合并**: 开发完成后合并回 develop

### bugfix/* 分支
- **用途**: Bug 修复
- **命名**: `bugfix/<问题描述>`
- **来源**: develop 分支
- **合并**: 修复完成后合并回 develop

### hotfix/* 分支
- **用途**: 生产环境紧急修复
- **命名**: `hotfix/<问题描述>`
- **来源**: main 分支
- **合并**: 同时合并到 main 和 develop

### release/* 分支
- **用途**: 版本发布准备
- **命名**: `release/v<版本号>`
- **来源**: develop 分支
- **合并**: 测试完成后合并到 main 和 develop

---

## 🔄 工作流程

### 开发新功能

```bash
# 1. 从 develop 创建功能分支
git checkout develop
git pull origin develop
git checkout -b feature/data-source-tushare

# 2. 开发功能并提交
git add .
git commit -m "feat: 实现 Tushare 数据源"

# 3. 推送到远程
git push -u origin feature/data-source-tushare

# 4. 创建 Pull Request 到 develop
# 等待 Code Review 通过后合并
```

### 修复 Bug

```bash
# 1. 从 develop 创建修复分支
git checkout develop
git pull origin develop
git checkout -b bugfix/order-status-error

# 2. 修复 Bug 并提交
git add .
git commit -m "fix: 修复订单状态更新错误"

# 3. 推送并创建 PR
git push -u origin bugfix/order-status-error
```

### 发布版本

```bash
# 1. 从 develop 创建发布分支
git checkout develop
git pull origin develop
git checkout -b release/v0.1.0

# 2. 进行最后测试和文档更新
git commit -m "docs: 更新 v0.1.0 发布说明"

# 3. 合并到 main
git checkout main
git merge --no-ff release/v0.1.0
git tag -a v0.1.0 -m "Release version 0.1.0"

# 4. 合并回 develop
git checkout develop
git merge --no-ff release/v0.1.0

# 5. 删除发布分支
git branch -d release/v0.1.0
git push origin --delete release/v0.1.0
```

### 紧急修复

```bash
# 1. 从 main 创建紧急修复分支
git checkout main
git pull origin main
git checkout -b hotfix/critical-trading-error

# 2. 修复问题
git commit -m "hotfix: 修复交易模块严重错误"

# 3. 合并到 main 并打标签
git checkout main
git merge --no-ff hotfix/critical-trading-error
git tag -a v0.1.1 -m "Hotfix for trading error"

# 4. 合并到 develop
git checkout develop
git merge --no-ff hotfix/critical-trading-error
```

---

## 📝 提交规范

### Commit Message 格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type 类型

| 类型 | 说明 |
|------|------|
| feat | 新功能 |
| fix | Bug 修复 |
| docs | 文档更新 |
| style | 代码格式 (不影响功能) |
| refactor | 重构 |
| test | 测试相关 |
| chore | 构建工具/依赖管理 |
| hotfix | 紧急修复 |

### 示例

```bash
# 新功能
git commit -m "feat(data): 实现 Tushare 数据源接入"

# Bug 修复
git commit -m "fix(engine): 修复回测引擎滑点计算错误"

# 文档更新
git commit -m "docs(readme): 更新安装说明"

# 重构
git commit -m "refactor(strategy): 优化策略基类结构"

# 紧急修复
git commit -m "hotfix(trading): 修复订单提交失败问题"
```

---

## 🛡️ 分支保护规则

### main 分支
- ✅ 需要 Pull Request
- ✅ 至少 1 人 Review
- ✅ 通过 CI/CD 检查
- ✅ 禁止强制推送

### develop 分支
- ✅ 需要 Pull Request
- ✅ 至少 1 人 Review
- ✅ 通过 CI 检查
- ✅ 禁止强制推送

---

## 📊 分支状态查看

```bash
# 查看本地分支
git branch

# 查看远程分支
git branch -r

# 查看所有分支
git branch -a

# 查看分支合并情况
git branch --merged

# 查看未合并分支
git branch --no-merged
```

---

## 🔧 常用命令

```bash
# 切换到 develop 分支
git checkout develop

# 拉取最新代码
git pull origin develop

# 创建并切换到新分支
git checkout -b feature/new-feature

# 合并分支
git merge feature/new-feature

# 删除本地分支
git branch -d feature/old-feature

# 删除远程分支
git push origin --delete feature/old-feature

# 查看提交历史
git log --oneline --graph --all
```

---

## 📌 注意事项

1. **不要直接在 main/develop 上开发**
   - 始终从 develop 创建功能分支

2. **保持分支更新**
   - 定期从 develop 拉取最新代码

3. **及时清理分支**
   - 合并后删除已完成的分支

4. **小步提交**
   - 每个 commit 只做一件事

5. **写清晰的提交信息**
   - 遵循提交规范

---

*Last Updated: 2026-03-18*
