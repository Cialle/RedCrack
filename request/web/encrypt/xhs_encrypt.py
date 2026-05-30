from request.web.encrypt.cookie.a1_and_webId import XHS_A1_And_WebId_Encrypt
from request.web.encrypt.cookie.gid_webprofile_data import XHS_Gid_Webprofile_Data_Encrypt
from request.web.encrypt.cookie.websectiga import XHS_Websectiga_Encrypt

from request.web.encrypt.header.X_B3 import XHS_XB3_Encrypt
from request.web.encrypt.header.X_Rap_Param import XHS_XRapParam_Encrypt
from request.web.encrypt.header.X_S import XHS_XS_Encrypt
from request.web.encrypt.header.X_S_Common import XHS_XSC_Encrypt
from request.web.encrypt.header.X_Xray import XHS_Xray_Encrypt

from request.web.encrypt.other.XhsFpGenerator import XhsFpGenerator


class XiaoHongShu_Encrypt(XHS_A1_And_WebId_Encrypt,
                          XHS_Gid_Webprofile_Data_Encrypt,
                          XHS_Websectiga_Encrypt,

                          XHS_XB3_Encrypt,
                          XHS_XRapParam_Encrypt,
                          XHS_XS_Encrypt,
                          XHS_XSC_Encrypt,
                          XHS_Xray_Encrypt,

                          XhsFpGenerator
                          ):
    """
    小红书加密
    """
    def __init__(self):
        XHS_A1_And_WebId_Encrypt.__init__(self)
        XHS_Gid_Webprofile_Data_Encrypt.__init__(self)
        XHS_Websectiga_Encrypt.__init__(self)

        XHS_XB3_Encrypt.__init__(self)
        XHS_XRapParam_Encrypt.__init__(self)
        XHS_XS_Encrypt.__init__(self)
        XHS_XSC_Encrypt.__init__(self)
        XHS_Xray_Encrypt.__init__(self)

        XhsFpGenerator.__init__(self)


#单例模式
xhs_encrypt = XiaoHongShu_Encrypt()