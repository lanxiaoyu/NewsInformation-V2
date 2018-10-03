import random
import re
from datetime import datetime
from flask import request, current_app, abort, make_response, jsonify, session
from info import redis_store, constants, db
from info.lib.yuntongxun.sms import CCP
from info.utils.captcha.captcha import captcha
from info.utils.response_code import RET
from . import passport_bp
from info.models import User


@passport_bp.route('/login_out', methods=['POST'])
def login_out():
    """退出登录后端接口"""
    # 将用户登录信息清除
    session.pop("user_id")
    session.pop("mobile")
    session.pop("nick_name")
    return jsonify({"errno":RET.OK, "errmsg": '退出登录成功'})



#127.0.0.1:8080/login
@passport_bp.route('/login', methods=['POST'])
def login():
    """用户登录的接口"""
    """
    1.获取参数
        1.1 mobile:手机号 password:密码
    2.检验参数
        2.1 非空判断
        2.2 手机号格式判断
    3.逻辑处理
        3.1 根据mobile查询用户在不在
        3.2 不存在:提示账户不存在
        3.3 存在:判断密码是否填写正确
        3.4 保存用户登录信息(更新最后一次登录时间)
    4.返回值
        4.1 登录成功
    """

    # 1.1 mobile: 手机号password: 密码
    param_dict = request.json

    mobile = param_dict.get("mobile")
    password = param_dict.get("password")

    # 2.1 非空判断
    if not all([mobile,password]):
        return jsonify({"errno":RET.PARAMERR, "errmsg": '参数不足'})

    #2.2 手机号格式检验
    if not re.match("1[35789][0-9]{9}$", mobile):
        current_app.logger.error("手机号格式错误")
        return jsonify({"errno":RET.PARAMERR, "errmsg": '手机号格式错误'})

    # 3.1 根据mobile查询用户名是否存在
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"errno":RET.DBERR, "errmsg": '数据库查询错误'})

    # 3.2 不存在:提示账户不存在
    if not user:
        return jsonify({"errno":RET.NODATA, "errmsg": '用户不存在'})

    # 3.3 存在:判断密码是否正确
    if not user.check_passowrd(password):
        # 密码错误
        return jsonify({"errno":RET.DATAERR, "errmsg": '密码错误'})

    # 3.4 保存登录信息
    session["user_id"] = user.id
    session["nick_name"] = user.nick_name
    session["mobile"] = user.mobile

    # 更新最后一次登录时间
    user.last_login = datetime.now()

    # 修改了user对象的数据，需要使用commit将数据保存到数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"errno":RET.DBERR, "errmsg": '数据库保存用户信息错误'})

    # 4.1 登录成功
    return jsonify({"errno":RET.OK, "errmsg": '登录成功'})


# 127.0.0.1:8080/passport/register
@passport_bp.route("/register",methods = ["POST"])
def register():
    """注册后端接口的实现"""
    """
    1.获取参数
        1.1  mobile  smscode   password
    2.校验参数 
        2.1 非空判断
        2.2 手机号格式判断
    3.逻辑处理
        3.1 根据""SMS_CODE_%s" % mobile"作为key去redis中获取真实的短信验证码,如果获取到,则删除库中的数据
        3.2 对比用户填写的
        3.3 不相等 提示验证码填写错误
        3.4 相等 :根据User类创建用户对象,并给其属性赋值   
        3.5 保存到mysql中
        3.6 一般需求:注册成功,自动登录,记录用户登录信息
    4.返回值:注册成功
    """

    # 1.1 获取参数
    param_dict = request.json

    mobile = param_dict.get("mobile")
    smscode = param_dict.get("smscode")
    password = param_dict.get("password")

    # 2 参数检验
    # 2.1 非空判断
    if not all([mobile,smscode,password]):
        return jsonify({"errno":RET.PARAMERR, "errmsg": '参数不足'})
    #2.2 手机号格式检验
    if not re.match("1[35789][0-9]{9}$", mobile):
        current_app.logger.error("手机号格式错误")
        return jsonify({"errno":RET.PARAMERR, "errmsg": '手机号格式错误'})

    # 3.1 根据""SMS_CODE_%s" % mobile"作为key去redis中获取真实的短信验证码
    try:
        real_smscode = redis_store.get("SMS_CODE_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"errno":RET.DATAERR, "errmsg": '数据库查询错误'})

    if real_smscode:
        redis_store.delete("SMS_CODE_%s" % mobile)
    else:
        return jsonify({"errno":RET.DATAERR, "errmsg": '短信验证码过期'})

    # 3.2 对比用户填写的
    if smscode != real_smscode:
        # 不相等
        return jsonify({"errno":RET.PARAMERR, "errmsg": '验证码填写错误'})
    else:
        # 相等  根据User类创建用户对象,并给其属性赋值   保持到mysql中
        user = User()
        user.mobile = mobile
        user.nick_name = mobile
        user.last_login = datetime.now()

        # 这一条代码实现了密码加密+保存到数据库
        user.password = password


        # 3.5
        try:
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()

        # 3.6 一般需求:注册成功,自动登录,记录用户登录信息
        session["user_id"] = user.id
        session["nick_name"] = user.nick_name
        session["mobile"] = user.id = user.mobile

        # 4 注册成功
        return jsonify({"errno":RET.OK, "errmsg": '注册成功'})


# 127.0.0.1:8080/passport/image_code?code_id=uuid编码
@passport_bp.route("image_code")
def get_image_code():
    """获取验证码图片的后端接口"""
    # 1.获取参数
    #     1.1获取code_id,全球唯一编码(uuid)
    code_id = request.args.get("code_id", "")

    # 2.校验参数
    #     2.1非空判断,判断code_id是否有值
    if not code_id:
        current_app.logger.error(" 参数不足")
        abort(404)

    # 3.逻辑处理
    #     3.1生成验证码图片 & 生成验证码图片的真实值
    image_name, real_image_code, image_data = captcha.generate_captcha()

    #     3.2以code_id作为key将生成的验证码图片的真实值保存到redis中
    try:
        redis_store.setex("imageCodeId_%s" % code_id, constants.IMAGE_CODE_REDIS_EXPIRES, real_image_code)
    except Exception as e:
        current_app.logger.error(e)
        abort(500)

    # 4.返回值
    #     4.1返回验证码图片(二进制图片数据,不能兼容所有浏览器)
    # 创建响应对象
    response = make_response(image_data)
    # 设置响应数据的类型为Content-Type："image/JPEG"
    response.headers["Content-Type"] = "image/JPEG"
    return response


# 127.0.0.1:8080/passport/sms_code
@passport_bp.route("/sms_code", methods=["POST"])
def send_sms_code():
    """点击发生短信验证码后端接口"""
    # 1.获取参数:上传数据是json类型
    # 1.1用户手机号mobile,用户填写的图片验证码:image_code,编号UUID:image_code_id
    # 可以接受前端上传的json格式数据，json字符串转换成python对象
    param_dict = request.json
    mobile = param_dict.get("mobile", "")
    image_code = param_dict.get("image_code", "")
    image_code_id = param_dict.get("image_code_id", "")

    # 2.检验参数
    # 2.1 非空判断 mobile image_code image_code_id 是否为空
    if not all([mobile, image_code, image_code_id]):
        current_app.logger.error("参数不足")
        return jsonify({"errno": RET.PARAMERR, "errmsg": '参数不足'})
        # 2.2 手机号格式的正则判断

    if not re.match('1[35789][0-9]{9}', mobile):
        current_app.logger.error(" 手机号格式错误")
        return jsonify({"errno": RET.PARAMERR, "errmsg": '手机号格式错误'})

    # 3.逻辑处理
    # 3.1 根据编号去redis数据库获取图片验证码的真实值(正确值)
    try:
        real_image_code = redis_store.get("imageCodeId_%s" % image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"errno": RET.DBERR, "errmsg": '从redis中获取图片真实值异常'})

        # 3.1.1 真实值有值:将这个值从redis中删除（防止他人多次拿着同一个验证码值来验证）
    if real_image_code:
        redis_store.delete("imageCodeId_%s" % image_code_id)

        # 3.1.2 真实值没有值： 图片验证码真实值过期了
    else:
        return jsonify({"errno": RET.NODATA, "errmsg": '图片验证码过期'})

        # 3.2 拿用户填写的图片验证码值和Redis中获取的真实值进行比较
        # 细节1：全部按照小写格式进行比较（忽略大小写）
        # 细节2：redis对象创建的时候设置decode_responses=True
    if real_image_code.lower() != image_code.lower():
        # 3.3不相等 告诉前端图片验证码填写错误
        return jsonify({"errno": RET.DATAERR, "errmsg": '验证码填写错误'})


    """# TODO: 判断用户是否注册过, 如果注册过，就不在发送短信验证码引导到登录页（提高用户体验）"""
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"errno": RET.DATAERR, "errmsg": '查询手机好出现问题'})

    if user:
        return jsonify({"errno":RET.DATAEXIST, "errmsg": '该手机号已注册'})

        # 3.4 相等:生成6位数验证码,发送短信
    sms_code = random.randint(0, 999999)
    # 位数不足补零
    sms_code = "%06d" % sms_code

    try:
        result = CCP().send_template_sms(mobile, {sms_code, constants.SMS_CODE_REDIS_EXPIRES / 60}, 1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"errno": RET.THIRDERR, "errmsg": '云通讯发送短信失败'})

    if result != 0:
        return jsonify({"errno": RET.THIRDERR, "errmsg": '云通讯发送短信失败'})

        # 3.5 将生成的6位随机短信吗储存到redis数据库中
    try:
        redis_store.setex("SMS_CODE_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify({"errno": RET.DATAERR, "errmsg": 'redis储存短信验证码异常'})

    # 4.返回值   发送短信验证码成功
    return jsonify({"errno": RET.OK, "errmsg": '短息发生成功'})
