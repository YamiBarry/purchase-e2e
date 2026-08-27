#!/bin/bash
# fast-test.sh — 快速编译+运行单个 Spock/Groovy 测试（绕过 Maven 生命周期）
#
# 原理：模拟 IDEA 的行为
#   1. groovyc 只编译改动的 .groovy 文件（不重新编译整个项目）
#   2. JUnit Platform 并行 8 线程跑测试
#   对比 mvn test：从 17s+ 降到 ~5s（3-5x 提速）
#
# 前提：先跑一次 mvn install -DskipTests -am 生成 target/classes
#
# 内置依赖：scripts/junit-platform-console-standalone-1.7.2.jar（无需联网下载）
#
# 用法:
#   ./fast-test.sh <项目根目录> <模块名> <测试文件路径>
#
# 参数说明:
#   项目根目录 — Maven 多模块项目的根目录（包含父 pom.xml）
#   模块名    — 测试所在的 Maven 模块目录名
#   测试文件  — 相对于模块目录的测试文件路径
#
# 示例:
#   # sellerportal-service
#   ./fast-test.sh /mnt/d/Documents/code/yamibuy/central-3p/seller/sellerportal-service \
#     central-sellerportal-service \
#     src/test/groovy/com/yamibuy/central/sellerportal/service/ShipmentServiceTest.groovy
#
#   # central-partner-service
#   ./fast-test.sh /mnt/d/Documents/code/yamibuy/central-partner-service \
#     central-partner-service \
#     src/test/groovy/com/yamibuy/central/partner/service/OnboardingAgreementServiceTest.groovy
#
#   # openapi-2.0
#   ./fast-test.sh /mnt/d/Documents/code/yamibuy/central-3p/openapi-2.0 \
#     central-openapi-service \
#     src/test/groovy/com/yamibuy/central/openapi/service/InventoryServiceTest.groovy

set -e

PROJECT_ROOT="${1:-.}"
MODULE_DIR="$2"
TEST_FILE="$3"

if [ -z "$TEST_FILE" ] || [ -z "$MODULE_DIR" ]; then
  echo "用法: $0 <项目根目录> <模块名> <测试文件路径>"
  echo ""
  echo "示例:"
  echo "  $0 /mnt/d/code/sellerportal-service central-sellerportal-service \\"
  echo "    src/test/groovy/com/yamibuy/central/sellerportal/service/ShipmentServiceTest.groovy"
  echo ""
  echo "前提: 先跑一次全量编译"
  echo "  cd <项目根目录> && mvn install -DskipTests -pl <模块名> -am -T 8"
  exit 1
fi

cd "$PROJECT_ROOT"

# 自动推断测试类全限定名
FULL_CLASS=$(echo "$TEST_FILE" | sed 's|.*/src/test/groovy/||' | sed 's|^src/test/groovy/||' | sed 's|\.groovy$||' | tr '/' '.')

echo "📦 项目: $PROJECT_ROOT"
echo "📦 模块: $MODULE_DIR"
echo "📄 文件: $MODULE_DIR/$TEST_FILE"
echo "🎯 类名: $FULL_CLASS"

# 检查 target/classes 是否存在
if [ ! -d "$MODULE_DIR/target/classes" ]; then
  echo ""
  echo "❌ $MODULE_DIR/target/classes 不存在"
  echo "   请先执行全量编译:"
  echo "   mvn install -DskipTests -pl $MODULE_DIR -am -T 8"
  exit 1
fi

# 生成 classpath（按项目+模块缓存，60 分钟有效）
CP_KEY=$(echo "$PROJECT_ROOT/$MODULE_DIR" | md5sum | cut -c1-8)
CP_CACHE="/tmp/fast-test-cp-${CP_KEY}.txt"
if [ ! -f "$CP_CACHE" ] || [ "$(find "$CP_CACHE" -mmin +60 2>/dev/null)" ]; then
  echo ""
  echo "⏳ 生成 classpath（缓存 60 分钟）..."
  mvn dependency:build-classpath -pl "$MODULE_DIR" -q -Dmdep.outputFile="$CP_CACHE" 2>/dev/null
fi

CP="$(cat $CP_CACHE):$MODULE_DIR/target/classes:$MODULE_DIR/target/test-classes"

# Step 1: groovyc 编译单个测试文件
echo ""
echo "🔨 编译 $TEST_FILE ..."
COMPILE_START=$(date +%s%N)
java -cp "$CP" org.codehaus.groovy.tools.FileSystemCompiler \
  -cp "$CP" \
  -d "$MODULE_DIR/target/test-classes" \
  "$MODULE_DIR/$TEST_FILE"
COMPILE_END=$(date +%s%N)
COMPILE_MS=$(( (COMPILE_END - COMPILE_START) / 1000000 ))
echo "   编译耗时: ${COMPILE_MS}ms"

# Step 2: Locate JUnit Platform Console Standalone
# Priority: scripts dir > /tmp cache > download
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STANDALONE_LOCAL="$SCRIPT_DIR/junit-platform-console-standalone-1.7.2.jar"
STANDALONE="/tmp/junit-platform-console-standalone-1.7.2.jar"

if [ -f "$STANDALONE_LOCAL" ]; then
  STANDALONE="$STANDALONE_LOCAL"
elif [ ! -f "$STANDALONE" ]; then
  echo ""
  echo "⬇️  下载 junit-platform-console-standalone（仅首次）..."
  curl -sL "https://repo1.maven.org/maven2/org/junit/platform/junit-platform-console-standalone/1.7.2/junit-platform-console-standalone-1.7.2.jar" -o "$STANDALONE"
fi

# Step 3: 并行 8 线程跑测试
echo ""
echo "🚀 运行测试（并行 8 线程）..."
TEST_START=$(date +%s%N)
java -jar "$STANDALONE" -cp "$CP" \
  --select-class="$FULL_CLASS" \
  --config=junit.jupiter.execution.parallel.enabled=true \
  --config=junit.jupiter.execution.parallel.mode.default=concurrent \
  --config=junit.jupiter.execution.parallel.config.strategy=fixed \
  --config=junit.jupiter.execution.parallel.config.fixed.parallelism=8 \
  --details=summary
TEST_END=$(date +%s%N)
TEST_MS=$(( (TEST_END - TEST_START) / 1000000 ))

echo ""
echo "📊 总结: 编译 ${COMPILE_MS}ms + 运行 ${TEST_MS}ms = 总计 $(( (COMPILE_MS + TEST_MS) / 1000 ))s"
