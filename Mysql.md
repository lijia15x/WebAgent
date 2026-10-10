# MySQL Docker 部署指南

适用环境：Ubuntu 20.04、Docker Compose、MySQL 8.4。

## 1. 安装 Docker

安装 Docker Engine 和 Docker Compose 插件后，确认命令可用：

```bash
sudo docker version
sudo docker compose version
```

## 2. 创建目录

```bash
sudo mkdir -p /opt/mysql/{data,conf.d,backup}
cd /opt/mysql
```

| 目录 | 用途 |
| --- | --- |
| `/opt/mysql/data` | 数据库文件 |
| `/opt/mysql/conf.d` | MySQL 配置 |
| `/opt/mysql/backup` | 数据库备份 |

## 3. 创建环境变量文件

编辑环境变量文件：

```bash
sudo vim /opt/mysql/.env
```

写入以下内容：

```dotenv
MYSQL_ROOT_PASSWORD=替换为第一个随机密码
MYSQL_DATABASE=app
MYSQL_USER=app
MYSQL_PASSWORD=替换为第二个随机密码
```

限制文件权限：

```bash
sudo chmod 600 /opt/mysql/.env
```

## 4. 创建 MySQL 配置

编辑配置文件：

```bash
sudo vim /opt/mysql/conf.d/my.cnf
```

写入以下内容：

```ini
[mysqld]
character-set-server=utf8mb4
collation-server=utf8mb4_0900_ai_ci
default-time-zone=+08:00

max_connections=200
slow_query_log=ON
long_query_time=2
log_error_verbosity=2

[client]
default-character-set=utf8mb4
```

## 5. 创建 Compose 配置

编辑 Compose 文件：

```bash
sudo vim /opt/mysql/compose.yaml
```

写入以下内容：

```yaml
services:
  mysql:
    image: mysql:8.4
    container_name: mysql
    restart: unless-stopped
    env_file:
      - .env
    ports:
      - "0.0.0.0:3306:3306"
    volumes:
      - /opt/mysql/data:/var/lib/mysql
      - /opt/mysql/conf.d:/etc/mysql/conf.d:ro
      - /opt/mysql/backup:/backup
    healthcheck:
      test:
        - CMD-SHELL
        - mysqladmin ping -h localhost -uroot -p"$${MYSQL_ROOT_PASSWORD}" --silent
      interval: 10s
      timeout: 5s
      retries: 10
      start_period: 30s
```

> `0.0.0.0:3306` 会监听所有 IPv4 网卡。必须通过服务器防火墙或公司防火墙限制访问来源，禁止向公网开放 3306。

## 6. 启动 MySQL

```bash
cd /opt/mysql
sudo docker compose pull
sudo docker compose up -d
sudo docker compose ps
sudo docker compose logs -f mysql
```

日志出现 `ready for connections` 后，按 `Ctrl+C` 退出日志查看。

## 7. 检查 MySQL

进入 MySQL：

```bash
sudo docker exec -it mysql mysql -uroot -p
```

执行检查：

```sql
SELECT VERSION();
SHOW DATABASES;
SHOW VARIABLES LIKE 'character_set_server';
SHOW VARIABLES LIKE 'collation_server';
```

## 8. 启用 root 远程登录

先进入容器内的 MySQL：

```bash
sudo docker exec -it mysql mysql -uroot -p
```

仅允许指定电脑登录。将 `192.168.10.50` 替换%（%为允许所有）为电脑的内网 IP：

```sql
ALTER USER 'root'@'%' IDENTIFIED BY '新的高强度密码';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;
SHOW GRANTS FOR 'root'@'%';
```

如果该账号已经存在，改用：

```sql
ALTER USER 'root'@'192.168.10.50' IDENTIFIED BY '替换为高强度密码';
GRANT ALL PRIVILEGES ON *.* TO 'root'@'192.168.10.50' WITH GRANT OPTION;
```

修改端口映射后必须重新创建容器：

```bash
cd /opt/mysql
sudo docker compose up -d --force-recreate
sudo ss -lntp | grep ':3306'
```

> 不要创建 `root`@`%`。在 MySQL 服务器防火墙或公司防火墙中，仅允许指定电脑访问 TCP 3306。

## 9. 备份与恢复

备份所有数据库：

```bash
cd /opt/mysql

sudo docker exec mysql sh -c \
  'exec mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" --single-transaction --routines --events --all-databases' \
  | sudo tee "/opt/mysql/backup/mysql-$(date +%F-%H%M%S).sql" >/dev/null
```

恢复备份：

```bash
cat /opt/mysql/backup/备份文件.sql \
  | sudo docker exec -i mysql sh -c \
    'exec mysql -uroot -p"$MYSQL_ROOT_PASSWORD"'
```