from config import config_dict
from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_session import Session

"""
 因为manage中需要传入 db,而db的产生需要传入app
 但是:
        if app is not None:
            self.init_app(app)     

        真正初始化的是init_app() 
 """
# 暂时没有app对象,就不会去初始化,只是声明一下
db = SQLAlchemy()
# 同样的方法,redis数据库的声明(全局变量)
redis_store = None  # type:StrictRedis

"工厂方法,传入配置名称--->返回对应的配置app对象"


def create_app(config_name):
    """创建app的方法,工厂方法"""
    # 1.创建app对象
    app = Flask(__name__)

    # 将配置类注册到app上
    config_class = config_dict[config_name]
    app.config.from_object(config_class)

    # 2.创建数据库对象
    # db = SQLAlchemy(app)
    db.init_app(app)

    # 3.创建redis数据库对象
    global redis_store
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

    return app
