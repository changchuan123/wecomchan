#!/bin/bash

# Git自动保存脚本 - WeComChan项目
# 使用方法: ./git_auto_save.sh [commit_message]

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取当前时间
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# 默认提交信息
DEFAULT_MESSAGE="WeComChan日常保存 - $TIMESTAMP"

# 如果提供了提交信息，使用它；否则使用默认信息
COMMIT_MESSAGE=${1:-"$DEFAULT_MESSAGE"}

echo -e "${BLUE}=== WeComChan Git自动保存脚本 ===${NC}"
echo -e "${YELLOW}时间: $TIMESTAMP${NC}"
echo -e "${YELLOW}提交信息: $COMMIT_MESSAGE${NC}"
echo ""

# 检查是否有变更
if git diff --quiet && git diff --cached --quiet; then
    echo -e "${GREEN}✓ 没有需要提交的变更${NC}"
    exit 0
fi

# 显示变更状态
echo -e "${BLUE}检测到的变更:${NC}"
git status --short
echo ""

# 添加所有变更
echo -e "${BLUE}添加所有变更...${NC}"
git add -A

# 检查是否有需要提交的文件
if git diff --cached --quiet; then
    echo -e "${YELLOW}没有需要提交的文件${NC}"
    exit 0
fi

# 提交变更
echo -e "${BLUE}提交变更...${NC}"
if git commit -m "$COMMIT_MESSAGE"; then
    echo -e "${GREEN}✓ 提交成功: $COMMIT_MESSAGE${NC}"
else
    echo -e "${RED}✗ 提交失败${NC}"
    exit 1
fi

# 显示提交历史
echo ""
echo -e "${BLUE}最近的提交历史:${NC}"
git log --oneline -5

echo ""
echo -e "${GREEN}=== WeComChan自动保存完成 ===${NC}" 