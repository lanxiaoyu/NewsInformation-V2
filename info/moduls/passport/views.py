from flask import request, current_app, abort, make_response
from info import redis_store, constants
from info.utils.captcha.captcha import captcha
from . import passport_bp


# 127.0.0.1:5000/passport/image_code?code_id=uuid编码
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
