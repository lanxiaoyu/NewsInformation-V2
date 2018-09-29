from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_session import Session
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from config import config_dict

# 1.创建app对象
app = Flask(__name__)

# 将配置类注册到app上
config_class = config_dict["development"]  # 有开发者决定当前所处的环境
app.config.from_object(config_class)

# 2.创建数据库对象
db = SQLAlchemy(app)

# 3.创建redis数据库对象
redis_store = StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT, db=config_class.REDIS_NUM)

# 4.开启csrf保护机制
"""
1.自动获取cookie中的csrf_token值
2.自动获取ajax请求头中的csrf_token
3.自己校验这2个值
"""
csrf = CSRFProtect(app)

# 5.创建session对象,将session的储存方法进行调整(flask后端内存-->redis数据库)
Session(app)

# 6.创建管理对象
manager = Manager(app)

# 7.数据库迁移对象
Migrate(app, db)

# 8.数据库迁移指令
manager.add_command("db", MigrateCommand)


@app.route('/index')
def index():
    return "index page"


if __name__ == '__main__':
    manager.run()
