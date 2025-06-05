#!/bin/bash

# 智能分析系统管理脚本
# 功能：启动、停止、重启和监控系统服务

# 配置
APP_NAME="智能分析系统"
APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_CMD="python"
SERVER_SCRIPT="web_server.py"
PID_FILE="${APP_DIR}/.server.pid"
LOG_FILE="${APP_DIR}/server.log"
MONITOR_INTERVAL=30  # 监控检查间隔（秒）

# 颜色配置
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

# 函数：显示帮助信息
show_help() {
    echo -e "${BLUE}${APP_NAME}管理脚本${NC}"
    echo "使用方法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start       启动服务"
    echo "  stop        停止服务"
    echo "  restart     重启服务"
    echo "  status      查看服务状态"
    echo "  monitor     以守护进程方式监控服务"
    echo "  logs        查看日志"
    echo "  help        显示此帮助信息"
}

# 函数：检查前置条件
check_prerequisites() {
    # 检查Python是否已安装
    if ! command -v $PYTHON_CMD &> /dev/null; then
        echo -e "${RED}错误: 未找到Python命令。请确保Python已安装且在PATH中。${NC}"
        exit 1
    fi

    # 检查server脚本是否存在
    if [ ! -f "${APP_DIR}/${SERVER_SCRIPT}" ]; then
        echo -e "${RED}错误: 未找到服务器脚本 ${SERVER_SCRIPT}。${NC}"
        echo -e "${YELLOW}当前目录: $(pwd)${NC}"
        exit 1
    fi
}

# 函数：获取进程ID
get_pid() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p $pid > /dev/null; then
            echo $pid
            return 0
        fi
    fi
    # 尝试通过进程名查找
    local pid=$(pgrep -f "python.*${SERVER_SCRIPT}" 2>/dev/null)
    if [ -n "$pid" ]; then
        echo $pid
        return 0
    fi
    echo ""
    return 1
}

# 函数：启动服务
start_server() {
    local pid=$(get_pid)
    if [ -n "$pid" ]; then
        echo -e "${YELLOW}警告: 服务已在运行 (PID: $pid)${NC}"
        return 0
    fi

    echo -e "${BLUE}正在启动${APP_NAME}...${NC}"
    cd "$APP_DIR"

    # 使用nohup在后台启动服务
    nohup $PYTHON_CMD $SERVER_SCRIPT > "$LOG_FILE" 2>&1 &
    local new_pid=$!

    # 保存PID到文件
    echo $new_pid > "$PID_FILE"

    # 等待几秒检查服务是否成功启动
    sleep 3
    if ps -p $new_pid > /dev/null; then
        echo -e "${GREEN}${APP_NAME}已成功启动 (PID: $new_pid)${NC}"
        return 0
    else
        echo -e "${RED}启动${APP_NAME}失败。查看日志获取更多信息: ${LOG_FILE}${NC}"
        return 1
    fi
}

# 函数：停止服务
stop_server() {
    local pid=$(get_pid)
    if [ -z "$pid" ]; then
        echo -e "${YELLOW}服务未运行${NC}"
        return 0
    fi

    echo -e "${BLUE}正在停止${APP_NAME} (PID: $pid)...${NC}"

    # 尝试优雅地停止服务
    kill -15 $pid

    # 等待服务停止
    local max_wait=10
    local waited=0
    while ps -p $pid > /dev/null && [ $waited -lt $max_wait ]; do
        sleep 1
        waited=$((waited + 1))
        echo -ne "${YELLOW}等待服务停止 $waited/$max_wait ${NC}\r"
    done
    echo ""

    # 如果服务仍在运行，强制停止
    if ps -p $pid > /dev/null; then
        echo -e "${YELLOW}服务未响应优雅停止请求，正在强制终止...${NC}"
        kill -9 $pid
        sleep 1
    fi

    # 检查服务是否已停止
    if ps -p $pid > /dev/null; then
        echo -e "${RED}无法停止服务 (PID: $pid)${NC}"
        return 1
    else
        echo -e "${GREEN}服务已成功停止${NC}"
        rm -f "$PID_FILE"
        return 0
    fi
}

# 函数：重启服务
restart_server() {
    echo -e "${BLUE}正在重启${APP_NAME}...${NC}"
    stop_server
    sleep 2
    start_server
}

# 函数：检查服务状态
check_status() {
    local pid=$(get_pid)
    if [ -n "$pid" ]; then
        local uptime=$(ps -o etime= -p $pid)
        local mem=$(ps -o %mem= -p $pid)
        local cpu=$(ps -o %cpu= -p $pid)

        echo -e "${GREEN}${APP_NAME}正在运行${NC}"
        echo -e "  PID:     ${BLUE}$pid${NC}"
        echo -e "  运行时间: ${BLUE}$uptime${NC}"
        echo -e "  内存使用: ${BLUE}$mem%${NC}"
        echo -e "  CPU使用:  ${BLUE}$cpu%${NC}"
        echo -e "  日志文件: ${BLUE}$LOG_FILE${NC}"
        return 0
    else
        echo -e "${YELLOW}${APP_NAME}未运行${NC}"
        return 1
    fi
}

# 函数：监控服务
monitor_server() {
    echo -e "${BLUE}开始监控${APP_NAME}...${NC}"
    echo -e "${BLUE}监控日志将写入: ${LOG_FILE}.monitor${NC}"
    echo -e "${YELLOW}按 Ctrl+C 停止监控${NC}"

    # 在后台启动监控
    (
        while true; do
            local pid=$(get_pid)
            local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

            if [ -z "$pid" ]; then
                echo "$timestamp - 服务未运行，正在重启..." >> "${LOG_FILE}.monitor"
                cd "$APP_DIR"
                $PYTHON_CMD $SERVER_SCRIPT >> "$LOG_FILE" 2>&1 &
                local new_pid=$!
                echo $new_pid > "$PID_FILE"
                echo "$timestamp - 服务已重启 (PID: $new_pid)" >> "${LOG_FILE}.monitor"
            else
                # 检查服务是否响应 (可以通过访问服务API实现)
                local is_responsive=true

                # 这里可以添加额外的健康检查逻辑
                # 例如：使用curl检查API是否响应
                # if ! curl -s http://localhost:8888/health > /dev/null; then
                #     is_responsive=false
                # fi

                if [ "$is_responsive" = false ]; then
                    echo "$timestamp - 服务无响应，正在重启..." >> "${LOG_FILE}.monitor"
                    kill -9 $pid
                    sleep 2
                    cd "$APP_DIR"
                    $PYTHON_CMD $SERVER_SCRIPT >> "$LOG_FILE" 2>&1 &
                    local new_pid=$!
                    echo $new_pid > "$PID_FILE"
                    echo "$timestamp - 服务已重启 (PID: $new_pid)" >> "${LOG_FILE}.monitor"
                fi
            fi

            sleep $MONITOR_INTERVAL
        done
    ) &

    # 保存监控进程PID
    MONITOR_PID=$!
    echo $MONITOR_PID > "${APP_DIR}/.monitor.pid"
    echo -e "${GREEN}监控进程已启动 (PID: $MONITOR_PID)${NC}"

    # 捕获Ctrl+C以停止监控
    trap 'kill $MONITOR_PID; echo -e "${YELLOW}监控已停止${NC}"; rm -f "${APP_DIR}/.monitor.pid"' INT

    # 等待监控进程
    wait $MONITOR_PID
}

# 函数：查看日志
view_logs() {
    if [ ! -f "$LOG_FILE" ]; then
        echo -e "${YELLOW}日志文件不存在: ${LOG_FILE}${NC}"
        return 1
    fi

    echo -e "${BLUE}显示最新的日志内容 (按Ctrl+C退出)${NC}"
    tail -f "$LOG_FILE"
}

# 主函数
main() {
    check_prerequisites

    local command=${1:-"help"}

    case $command in
        start)
            start_server
            ;;
        stop)
            stop_server
            ;;
        restart)
            restart_server
            ;;
        status)
            check_status
            ;;
        monitor)
            monitor_server
            ;;
        logs)
            view_logs
            ;;
        *)
            show_help
            ;;
    esac
}

# 执行主函数
main "$@"