from config import config_dict
from flask import Flask, session, g, render_template
from flask_sqlalchemy import SQLAlchemy
from redis import StrictRedis
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_session import Session
import logging
from logging.handlers import RotatingFileHandler

from info.utils.common import do_index_class, user_login_data

"""
 因为manage中需要传入 db,而db的产生需要传入app
 但是:
        if app is not None:
            self.init_app(app)     

        真正初始化的是init_app() 
 """
# 暂时没有app对象,就不会去初始化,只是声明一下
db = SQLAlchemy()

# 同样的方法,redis数据库的声明(全局变量),
# 因为在视图函数中使用redis存储kv数据时需要导入
redis_store = None  # type:StrictRedis

"工厂方法,传入配置名称--->返回对应的配置app对象"


def set_log(config_name):
    """记录日志的配置"""
    # 因为不同的环境会用到不同的日志级别,所以需要传入当前所处环境名称
    config_class = config_dict[config_name]

    # 设置日志的记录级别:config_class.LOG_LEVEL-->config.py中LOG_LEVEL(类属性)
    logging.basicConfig(level=config_class.LOG_LEVEL)

    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)

    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    # DEBUG manage.py  18 123
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')

    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)

    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


def create_app(config_name):
    """创建app的方法,工厂方法"""
    # 0.记录日志
    set_log(config_name)

    # 1.创建app对象
    app = Flask(__name__)

    # 将配置类注册到app上
    config_class = config_dict[config_name]
    app.config.from_object(config_class)

    # 2.创建数据库对象
    # db = SQLAlchemy(app)
    db.init_app(app)

    # 3.创建redis数据库对象
    # decode_responses=True 能够将二进制数据decode成字符串返回
    global redis_store
    redis_store = StrictRedis(host=config_class.REDIS_HOST,
                              port=config_class.REDIS_PORT,
                              db=config_class.REDIS_NUM,
                              decode_responses=True)

    # 4.开启csrf保护机制
    """
    1.自动获取cookie中的csrf_token值
    2.自动获取ajax请求头中的csrf_token
    3.自己校验这2个值
    """
    csrf = CSRFProtect(app)

    # 使用钩子函数将csrf_token带回给浏览器
    @app.after_request
    def set_csrftoken(response):
        """借助response.setcookie方法将csrf_token存储到浏览器"""
        # 1. 生成csrf_token随机值
        csrf_token =  generate_csrf()
        # 2. 设置cookie
        response.set_cookie("csrf_token",csrf_token)
        # 3.返回给响应对象
        return response

    # 自动捕获404错误,页面统一处理
    @app.errorhandler(404)
    @user_login_data
    def error_handle(err):
        user = g.user
        # 2.对象转成字典
        data = {
             "user_info": user.to_dict() if user else None                                 }
         # 3.渲染模板

        return render_template("news/404.html", data=data)



    # 添加自定义的过滤器
    app.add_template_filter(do_index_class,"do_index_class")

    # 5.创建session对象,将session的储存方法进行调整(flask后端内存-->redis数据库)
    Session(app)

    # 注册蓝图
    from info.moduls.index import index_bp  # 解决循环导入问题,因为导入别的模块时,到他时 他卡住了redis_store的创建
    # 放在这里的原因是index_app只在这里才用的上
    app.register_blueprint(index_bp)

    from info.moduls.passport import passport_bp
    app.register_blueprint(passport_bp)

    from info.moduls.news import news_bp
    app.register_blueprint(news_bp)
    return app
