# ManuScript Makefile
# 常用开发命令

.PHONY: help install run-v01 run-v02 run-v10 run-v20 test clean

# 默认显示帮助
help:
	@echo "ManuScript 开发命令"
	@echo ""
	@echo "安装依赖:"
	@echo "  make install-v01    安装 v0.1 依赖"
	@echo "  make install-v02    安装 v0.2 依赖"
	@echo "  make install-v10    安装 v1.0 依赖"
	@echo "  make install-v20    安装 v2.0 依赖"
	@echo ""
	@echo "运行:"
	@echo "  make proto-v01      运行 v0.1 prototype（无 UI）"
	@echo "  make run-v01        运行 v0.1 Gradio UI"
	@echo "  make run-v02        运行 v0.2"
	@echo "  make run-v10        运行 v1.0"
	@echo "  make run-v20        运行 v2.0"
	@echo ""
	@echo "测试:"
	@echo "  make test-v01       测试 v0.1"
	@echo "  make test-v02       测试 v0.2"
	@echo "  make test-v10       测试 v1.0"
	@echo "  make test-v20       测试 v2.0"
	@echo "  make test-all       运行所有测试"
	@echo ""
	@echo "其他:"
	@echo "  make clean          清理缓存文件"
	@echo "  make eval           运行评测对比"

# ===== 安装依赖 =====
install-v01:
	pip install -r legacy/v0_1/requirements.txt

install-v02:
	pip install -r legacy/v0_2/requirements.txt

install-v10:
	pip install -r legacy/v1_0/requirements.txt

install-v20:
	pip install -r legacy/v2_0/requirements.txt

# ===== 运行 =====
proto-v01:
	python legacy/v0_1/prototype.py

run-v01:
	python legacy/v0_1/main.py

run-v02:
	python legacy/v0_2/main.py

run-v10:
	python legacy/v1_0/main.py

run-v20:
	python legacy/v2_0/main.py

# ===== 测试 =====
test-v01:
	pytest legacy/v0_1/tests/ -v

test-v02:
	pytest legacy/v0_2/tests/ -v

test-v10:
	pytest legacy/v1_0/tests/ -v

test-v20:
	pytest legacy/v2_0/tests/ -v

test-all:
	pytest . -v

# ===== 评测 =====
eval:
	python evaluation/compare.py

# ===== 清理 =====
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
