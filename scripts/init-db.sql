-- 量化交易实验室 - PostgreSQL 初始化脚本
-- Quantitative Trading Lab - Database Initialization

-- 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ==================== 用户表 ====================
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'researcher',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- ==================== 策略表 ====================
CREATE TABLE strategies (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    user_id BIGINT REFERENCES users(id),
    code TEXT,
    parameters JSONB,
    status VARCHAR(20) DEFAULT 'draft',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_strategies_user_id ON strategies(user_id);
CREATE INDEX idx_strategies_status ON strategies(status);

-- ==================== 回测任务表 ====================
CREATE TABLE backtest_tasks (
    id BIGSERIAL PRIMARY KEY,
    strategy_id BIGINT REFERENCES strategies(id),
    symbol VARCHAR(20) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital DECIMAL(15,2) DEFAULT 1000000.00,
    commission_rate DECIMAL(10,6) DEFAULT 0.0003,
    slippage_rate DECIMAL(10,6) DEFAULT 0.001,
    status VARCHAR(20) DEFAULT 'pending',
    result JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_backtest_tasks_strategy_id ON backtest_tasks(strategy_id);
CREATE INDEX idx_backtest_tasks_status ON backtest_tasks(status);

-- ==================== 订单表 ====================
CREATE TABLE orders (
    id BIGSERIAL PRIMARY KEY,
    order_id VARCHAR(50) UNIQUE NOT NULL,
    user_id BIGINT REFERENCES users(id),
    strategy_id BIGINT REFERENCES strategies(id),
    symbol VARCHAR(20) NOT NULL,
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('buy', 'sell')),
    offset VARCHAR(10) NOT NULL CHECK (offset IN ('open', 'close')),
    order_type VARCHAR(20) NOT NULL CHECK (order_type IN ('limit', 'market', 'stop')),
    price DECIMAL(10,4),
    quantity BIGINT NOT NULL,
    filled_quantity BIGINT DEFAULT 0,
    filled_price DECIMAL(10,4),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    exchange_order_id VARCHAR(50),
    error_msg TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_orders_order_id ON orders(order_id);
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_symbol ON orders(symbol);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at);

-- ==================== 成交表 ====================
CREATE TABLE trades (
    id BIGSERIAL PRIMARY KEY,
    trade_id VARCHAR(50) UNIQUE NOT NULL,
    order_id VARCHAR(50) REFERENCES orders(order_id),
    user_id BIGINT REFERENCES users(id),
    strategy_id BIGINT REFERENCES strategies(id),
    symbol VARCHAR(20) NOT NULL,
    direction VARCHAR(10) NOT NULL,
    price DECIMAL(10,4) NOT NULL,
    quantity BIGINT NOT NULL,
    commission DECIMAL(10,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trades_trade_id ON trades(trade_id);
CREATE INDEX idx_trades_order_id ON trades(order_id);
CREATE INDEX idx_trades_user_id ON trades(user_id);
CREATE INDEX idx_trades_created_at ON trades(created_at);

-- ==================== 持仓表 ====================
CREATE TABLE positions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    strategy_id BIGINT REFERENCES strategies(id),
    symbol VARCHAR(20) NOT NULL,
    direction VARCHAR(10) NOT NULL,
    quantity BIGINT NOT NULL,
    avg_price DECIMAL(10,4) NOT NULL,
    market_value DECIMAL(15,2),
    unrealized_pnl DECIMAL(15,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, strategy_id, symbol, direction)
);

CREATE INDEX idx_positions_user_id ON positions(user_id);
CREATE INDEX idx_positions_symbol ON positions(symbol);

-- ==================== 资金流水表 ====================
CREATE TABLE account_flows (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    strategy_id BIGINT REFERENCES strategies(id),
    flow_type VARCHAR(20) NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    balance DECIMAL(15,2) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_account_flows_user_id ON account_flows(user_id);
CREATE INDEX idx_account_flows_created_at ON account_flows(created_at);

-- ==================== 风险预警表 ====================
CREATE TABLE risk_alerts (
    id BIGSERIAL PRIMARY KEY,
    alert_id VARCHAR(50) UNIQUE NOT NULL,
    user_id BIGINT REFERENCES users(id),
    strategy_id BIGINT REFERENCES strategies(id),
    alert_type VARCHAR(50) NOT NULL,
    alert_level VARCHAR(20) NOT NULL CHECK (alert_level IN ('info', 'warning', 'critical')),
    message TEXT NOT NULL,
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_risk_alerts_user_id ON risk_alerts(user_id);
CREATE INDEX idx_risk_alerts_level ON risk_alerts(alert_level);
CREATE INDEX idx_risk_alerts_created_at ON risk_alerts(created_at);

-- ==================== 操作日志表 ====================
CREATE TABLE operation_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    action VARCHAR(50) NOT NULL,
    resource VARCHAR(100),
    resource_id BIGINT,
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_operation_logs_user_id ON operation_logs(user_id);
CREATE INDEX idx_operation_logs_action ON operation_logs(action);
CREATE INDEX idx_operation_logs_created_at ON operation_logs(created_at);

-- ==================== 系统配置表 ====================
CREATE TABLE system_configs (
    id BIGSERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==================== 插入初始数据 ====================

-- 默认管理员账户 (密码需要哈希处理，这里仅示例)
INSERT INTO users (username, email, password_hash, role) VALUES
('admin', 'admin@quant-lab.com', '$2b$12$placeholder_hash', 'admin');

-- 系统配置
INSERT INTO system_configs (config_key, config_value, description) VALUES
('trading', '{"mode": "paper", "initial_capital": 1000000}', '交易配置'),
('risk', '{"max_position_ratio": 0.3, "max_daily_loss": 50000}', '风控配置'),
('data', '{"update_time": "02:00", "retention_days": 365}', '数据配置');

-- ==================== 创建触发器函数 ====================

-- 自动更新 updated_at 字段
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为需要自动更新时间的表添加触发器
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_strategies_updated_at
    BEFORE UPDATE ON strategies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at
    BEFORE UPDATE ON orders
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_positions_updated_at
    BEFORE UPDATE ON positions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_system_configs_updated_at
    BEFORE UPDATE ON system_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ==================== 创建视图 ====================

-- 用户策略统计视图
CREATE VIEW user_strategy_stats AS
SELECT 
    u.id as user_id,
    u.username,
    COUNT(DISTINCT s.id) as total_strategies,
    COUNT(DISTINCT CASE WHEN s.status = 'active' THEN s.id END) as active_strategies,
    COUNT(DISTINCT bt.id) as total_backtests,
    SUM(CASE WHEN bt.result->>'total_return' IS NOT NULL THEN 1 ELSE 0 END) as completed_backtests
FROM users u
LEFT JOIN strategies s ON u.id = s.user_id
LEFT JOIN backtest_tasks bt ON s.id = bt.strategy_id
GROUP BY u.id, u.username;

-- 当日交易统计视图
CREATE VIEW daily_trade_stats AS
SELECT 
    DATE(created_at) as trade_date,
    COUNT(*) as total_trades,
    SUM(CASE WHEN direction = 'buy' THEN 1 ELSE 0 END) as buy_trades,
    SUM(CASE WHEN direction = 'sell' THEN 1 ELSE 0 END) as sell_trades,
    SUM(quantity * price) as total_amount
FROM trades
GROUP BY DATE(created_at)
ORDER BY trade_date DESC;

-- ==================== 授权 ====================

-- 创建只读用户
CREATE USER quant_reader WITH PASSWORD 'read_only_password';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO quant_reader;

-- 创建普通用户
CREATE USER quant_user_rw WITH PASSWORD 'read_write_password';
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO quant_user_rw;

-- 注释
COMMENT ON DATABASE quant_lab IS '量化交易实验室 - 主数据库';
