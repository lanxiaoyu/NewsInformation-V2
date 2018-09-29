from info import redis_store
from . import index_bp
from info.models import User
from flask import render_template, current_app


# 2.使用蓝图对象
@index_bp.route('/')
def index():
    return render_template("news/index.html")


@index_bp.route("/favicon.ico")
def favico():
    """返回网页图标"""
    """
    Function used internally to send static files from the static
    这个方法是被内部用来发送静态文件到浏览器的
    """
    return current_app.send_static_file("news/favicon.ico")
