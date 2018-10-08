from flask import session, current_app, jsonify, g

from info.utils.response_code import RET


def do_index_class(index):
    """根据index下标返回对应的class值"""

    if index == 1:
        return "first"

    elif index == 2:
        return "second"

    elif index == 3:
        return "third"

    else:
        return ""


# 获取当前登录用户信息的装饰器
def user_login_data(view_func):
    def wrapper(*args,**kwargs):
        # 1 实现装饰器该完成的新功能
        user_id = session.get("user_id")

        user = None  # type:User

        # 进行延迟导入,解决循环导入db的问题
        from  info.models import User
        if user_id:
            try:
                # 获取用户对象
                user = User.query.get(user_id)
            except Exception as e:
                current_app.logger.error(e)
                return jsonify({"errno": RET.DBERR, "errmsg": '数据库查询用户错误'})

        # 将用户对象保存到g对象中
        g.user = user

        # 2 实现原有函数的基本功能
        result = view_func(*args,**kwargs)
        return result

    return wrapper