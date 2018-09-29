from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_session import Session


class Config(object):
    DEBUG = True

    # mysql数据库的配置信息
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@127.0.0.1:3306/NewsInformation_v2"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # redis数据库的配置信息
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379
    REDIS_NUM = 1

    SECRET_KEY = "DSFYGHEGEHJOUHGJIBRREJBJ"

    # 通过flask-session扩展.,将flask中的session(内存)调整到redis的配置信息
    # <1>储存数据库类型:redis
    SESSION_TYPE = "redis"
    # <2>将redis实例对象进行传入
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_NUM)
    # <3>对session数据进行加密,需要配置SECRET_KEY
    SESSION_USE_SIGNER = True
    # <4>关闭永久储存
    SESSION_PERMANENT = False
    # <5>过期时长(24小时)
    PERMANENT_SESSION_LIFETIME = 86400


# 1.创建app对象
app = Flask(__name__)

# 将配置类注册到app上
app.config.from_object(Config)

# 2.创建数据库对象
db = SQLAlchemy(app)

# 3.创建redis数据库对象
redis_store = StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=Config.REDIS_NUM)

# 4.开启csrf保护机制
"""
1.自动获取cookie中的csrf_token值
2.自动获取ajax请求头中的csrf_token
3.自己校验这2个值
"""
csrf = CSRFProtect(app)

# 5.创建session对象,将session的储存方法进行调整(flask后端内存-->redis数据库)
Session(app)


@app.route('/index')
def index():
    return "index page"


if __name__ == '__main__':
    app.run()
