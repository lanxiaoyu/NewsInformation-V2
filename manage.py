from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import create_app, db

app = create_app("development")  # # 有开发者决定当前所处的环境,工厂模式:传入什么配置,就返回对应的app配置对象

# 6.创建管理对象
manager = Manager(app)

# 7.数据库迁移对象
Migrate(app, db)

# 8.数据库迁移指令q
manager.add_command("db", MigrateCommand)

if __name__ == '__main__':
    manager.run()