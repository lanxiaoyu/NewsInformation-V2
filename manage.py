from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import create_app, db
from flask import current_app, jsonify
from info.models import User
from info.utils.response_code import RET

app = create_app("development")  # # 有开发者决定当前所处的环境,工厂模式:传入什么配置,就返回对应的app配置对象

# 6.创建管理对象
manager = Manager(app)

# 7.数据库迁移对象
Migrate(app, db)

# 8.数据库迁移指令q
manager.add_command("db", MigrateCommand)
"""使用方法:
    python3 manage.py createsuperuser -n "账号" -p '密码'
    python3 manage.py createsuperuser -name "账号" -password '密码'
     
     """


@manager.option('n', "--name", dest="name")
@manager.option('n', "--password", dest="password")
def createsuperuser(name, password):
    """创建管理员用户对象"""
    if not all([name, password]):
        return "参数不足"
    # 创建管理用户对象
    admin_user = User()
    admin_user.nick_name = name
    admin_user.mobile = name
    admin_user.password = password
    # 设置用户对象为管理员
    admin_user.is_admin = True

    # 保存到数据库
    try:
        db.session.add(admin_user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify({"errno": RET.DBERR, "errmsg": '保存管理员用户失败'})

    return "创建管理员用户成功"


if __name__ == '__main__':
    manager.run()
