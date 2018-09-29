from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import create_app, db
import logging
from flask import current_app

app = create_app("development")  # # 有开发者决定当前所处的环境,工厂模式:传入什么配置,就返回对应的app配置对象

# 6.创建管理对象
manager = Manager(app)

# 7.数据库迁移对象
Migrate(app, db)

# 8.数据库迁移指令
manager.add_command("db", MigrateCommand)


@app.route('/index')
def index():
    logging.debug("我是debug级别日志")
    logging.info("我是infog级别日志")
    logging.warning("我是warning级别日志")
    logging.error("我是error级别日志")
    logging.critical("我是critical级别日志")

    # flask中对logging模块进行了封装,直接用current_app调用,常用的方法
    current_app.logger.debug("falsk中记录的debug日志")
    return "index page"


if __name__ == '__main__':
    manager.run()
