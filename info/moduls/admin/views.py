from . import admin_bp
from flask import render_template

#/admin/login
@admin_bp.route('/login')
def admin_login():
    """
   后台管理登录接口
    """
    return render_template("admin/login.html")
