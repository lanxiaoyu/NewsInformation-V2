from flask import g, render_template, request, current_app, jsonify
from info.models import User
from info.utils.response_code import RET
from . import profile_bp
from info import user_login_data, db, constants
from info.moduls.profile import profile_bp
from info.utils.pic_storage import pic_storage
from info.models import Category


@profile_bp.route('/news_release', methods=['GET', 'POST'])
@user_login_data
def news_release():
    """新闻发布的后端接口"""
    """获取用户对象"""
    user = g.user
    # GET请求：展示新闻发布页面
    if request.method == 'GET':
        # 查询分类数据
        try:
            categories = Category.query.all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify({"errno": RET.DBERR, "errmsg": '查询分类数据异常'})
        # 对象列表转字典列表
        category_dict_list = []
        for category in categories if categories else []:
            category_dict_list.append(category.to_dict())

            #注意: 移除最新分类
        category_dict_list.pop(0)

        #组织响应数据
        data = {
            "categories":category_dict_list
        }
        return render_template("profile/user_news_release.html")

    # /user/collection?p=页码


@profile_bp.route('/collection')
@user_login_data
def user_collection_news():
    """获取当前用户新闻收藏列表数据"""

    """
    1.获取参数
        1.1  user :当前用户对象, p:当前页码(默认值第一页)
    2.校验参数
        2.1 非空判断
    3.逻辑处理
        3.0 根据user.collection_news,进行分页查询
    4.返回值
    """
    # 获取用户对象
    user = g.user
    p = request.args.get('p', 1)
    # 2.1参数类型判断
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"errno": RET.PARAMERR, "errmsg": '参数内容错误'})
    # 当前用户存在的时候采取查询

    """
    lazylazy="dynamic"设置后：
   如果没有真实用到user.collection_news，他就是一个查询对象
   如果真实用到user.collection_news，他就是一个列表
    """
    news_collections = []
    current_page = 1
    total_page = 1
    if user:
        try:
            paginate = user.collection_news.paginate(p, constants.USER_COLLECTION_MAX_NEWS, False)
            # 当前页码所有数据
            news_collections = paginate.items
            # 当前页码
            current_page = paginate.page
            # 总页数
            total_page = paginate.pages

        except Exception as e:
            current_app.logger.error(e)
            return jsonify({"errno": RET.DBERR, "errmsg": ''})
    # 对象列表转字典列表
    news_dict_collections = []
    for news in news_collections if news_collections else []:
        news_dict_collections.append(news.to_basic_dict())

    # 组织响应数据
    data = {
        "collections": news_dict_collections,
        "current_page": current_page,
        "total_page": total_page
    }
    # 4.返回值
    return render_template("profile/user_collection.html", data=data)


@profile_bp.route('/pass_info', methods=['GET', 'POST'])
@user_login_data
def pass_info():
    """修改密码后端接口"""
    user = g.user
    # GET请求：返回修改密码页面
    if request.method == 'GET':
        return render_template("profile/user_pass_info.html")

    # POST请求：修改用户密码接口
    """
    1.获取参数
        1.1 old_password:旧密码，new_password: 新密码，user:用户对象
    2.校验参数
        2.1 非空判断
    3.逻辑处理
        3.0 对旧密码进行校验
        3.1 将新密码赋值到user对象password属性上
        3.2 保存回数据库
    4.返回值
    """
    # 1.1 old_password:旧密码，new_password: 新密码，user:用户对象
    old_password = request.json.get("old_password")
    new_password = request.json.get("new_password")

    # 2.1 非空判断
    if not all([old_password, new_password]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不足")

    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")
    # 3.0 对旧密码进行校验
    if not user.check_passowrd(old_password):
        return jsonify(errno=RET.DATAERR, errmsg="旧密码填写错误")

    # 3.1 将新密码赋值到user对象password属性上
    user.password = new_password
    # 3.2 保存回数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存用户密码异常")
    # 4.返回值
    return jsonify(errno=RET.OK, errmsg="修改密码成功")


# 0.0.0:8000/user/info
@profile_bp.route('/pic_info', methods=['GET', 'POST'])
@user_login_data
def pic_info():
    """修改用户头像后端接口"""
    # 获取当前用户对象
    user = g.user
    # GET请求:返回修改用户头像页面
    if request.method == "GET":
        return render_template("profile/user_pic_info.html")

    """
     # POST请求：修改用户头像接口
      1.获取参数
          1.1  avatar :用户头像数据   user:用户对象
      2.检验参数
          2.1 非空判断
      3.逻辑处理
          3.0 借助封装好的工具,将二进制图片数据上传到七牛云
          3.1 图片的url保存到用户对象中
          3.2 将完整的图片url返回给前端
      4.返回值
      """
    # 1.1  avatar :用户头像数据   user:用户对象
    try:
        pic_data = request.files.get("avatar").read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"errno": RET.PARAMERR, "errmsg": '图片数据不存在'})

    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    # 3.0  借助封装好的工具, 将二进制图片数据上传到七牛云
    try:
        pic_name = pic_storage(pic_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"errno": RET.THIRDERR, "errmsg": '七牛云上传图片失败'})

    """
     1. avatar_url = 域名 + 图片名称
     2. avatar_url = 图片名称  （采用该方法更换域名更加方便）
    """

    # 3.1  图片的url保存到用户对象中
    user.avatar_url = pic_name
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify({"errno": RET.DBERR, "errmsg": '保存用户头像失败'})

    # 3.2  将完整的图片url返回给前端
    full_rul = constants.QINIU_DOMIN_PREFIX + pic_name
    # 组织数据
    data = {
        "avatar_url": full_rul
    }
    return jsonify(errno=RET.OK, errmsg='修改用户头像成功', data=data)


# 0.0.0:8000/user/info
@profile_bp.route('/base_info', methods=['GET', 'POST'])
@user_login_data
def user_base_info():
    """展示用户基本资料页面"""
    # 获取用户对象
    user = g.user
    # get 请求查询用户基本资料并展示
    if request.method == "GET":
        data = {
            "user_info": user.to_dict() if user else None
        }
        return render_template("profile/user_base_info.html", data=data)


# 0.0.0:8000/user/info
@profile_bp.route('/info')
@user_login_data
def user_info():
    """
    展示用户个人中心页面"""
    # 1.获取用户对象
    user = g.user

    # 2. 组织数据
    data = {
        "user_info": user.to_dict() if user else None
    }
    return render_template("profile/user.html", data=data)
