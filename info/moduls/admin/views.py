from flask import current_app
from flask import request, jsonify, redirect, url_for
from flask import session
from info import db
from info.models import User
from info.utils.response_code import RET
from . import admin_bp
from flask import render_template


# /admin/index
@admin_bp.route('/index')
def admin_index():
    """后台管理首页"""
    return render_template("admin/index.html")


# /admin/login
@admin_bp.route('/login', methods=['POST', 'GET'])
def admin_login():
    """后台管理登录接口"""
    # get请求：展示登录页
    if request.method == "GET":
        return render_template("admin/login.html")
    # post请求：管理员登录业务逻辑处理
    """
    1.获取参数
        1.1 username: 账号， password:密码
    2.校验参数
        2.1 非空判断
    3.逻辑处理
        3.0 根据username查询用户
        3.1 name.check_password进行密码校验
        3.2 管理员用户数据保存到session
    4.返回值
        4.1 跳转到管理首页
    """
    # 1.1 username: 账号， password:密码
    username = request.form.get("username")
    password = request.form.get("password")
    # 2.1 非空判断
    if not all([username, password]):
        return render_template("admin/login.html", errmsg="参数不足")

    # 3.0 根据username查询用户
    try:
        admin_user = User.query.filter(User.mobile == username, User.is_admin == True).first()
    except Exception as e:
        current_app.logger.error(e)
        return render_template("admin/login.html", errmsg="查询管理员用户对象异常")
    if not admin_user:
        return render_template("admin/login.html", errmsg="管理员用户不存在")

    # 3.1 user.check_password进行密码校验
    if not admin_user.check_passowrd(password):
        return render_template("admin/login.html", errmsg="密码填写错误")
    # 保存回数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return render_template("admin/login.html", errmsg="保存用户对象异常")

    # 3.2 管理员用户数据保存到session
    session["nick_name"] = username
    session["user_id"] = admin_user.id
    session["mobile"] = username
    session["is_admin"] = True

    # 4.重定向到管理首页
    return redirect(url_for("admin.admin_index"))
