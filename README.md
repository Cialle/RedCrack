# ⚙️ RedCrack

<div align="center">
小红书 Web端 全站 所有加密参数 Python 纯算逆向。
    </div>


---

## 📜 项目简介 (Introduction)

本项目旨在通过深入研究小红书平台所采用的数据保护及反爬虫机制，学习并理解其中涉及的安全风控技术和逆向工程技术原理。
我们将分析这些机制如何有效防止非授权访问与数据抓取，从而更好地认识到构建安全网络环境的重要性。
在此基础上，我们希望探讨如何合法合规地开发出更高效的数据收集解决方案，促进互联网行业的健康发展。
整个过程中，我们将严格遵守相关法律法规，尊重所有平台的服务条款，确保研究活动符合道德标准。

**注意：** 本项目中的代码是基于对**公开可访问**的JavaScript代码进行分析和**独立实现**的，不包含任何受版权保护的**原创代码或商业秘密**。

**侵权移除通知机制：** 若本项目的任何代码或内容被第三方权利人认为侵犯了其合法权益（包括但不限于著作权、数据权益等），请权利人务必通过以下方式联系作者，提供详细的侵权证明：

- **联系邮箱：** fengxi9264@gmail.com   · **（不接该项目相关单子，请不要联系我）**

- **通知要求：** 请提供详细的侵权内容链接、权利证明文件及移除要求。 

作者承诺，在收到合格的侵权通知并核实后，将**立即**对涉嫌侵权的代码部分进行移除或修改。

## 🚀 主要功能 (Features)

* 逆向所有参数

  * Cookies:
    * `a1`
    * `webId`
    * `acw_tc`
    * `web_session` (游客生成)
    * `sec_poison_id`
    * `websectiga`
    * `gid`

  * headers:
    * `x-b3-traceid`
    * `x-s`
    * `x-s-common`
    * `x-t`
    * `x-xray-traceid`

* 采用 `aiohttp` 封装异步 `session`

* 封装大部分常用接口，简单使用 `xhs_session.apis.note.like_note(note_id)` 即可调用

* 预留 app 操作位置， 例如 扫码登录 / 124安全扫码 等 只需要根据注释掉的代码补全你自己的app协议即可。

  

## ⚠️ 法律及风险免责声明 (Legal and Risk Disclaimer)

**请仔细阅读并理解以下条款：**

1.  **目的限定：** 本项目代码**仅供个人学习、技术研究和交流使用**。
2.  **严禁滥用：** **严禁**将本项目用于**任何商业用途、非法用途、恶意用途**，或对任何第三方网站进行**攻击、破坏其正常服务或获取未经授权的数据**。
3.  **用户责任：** 任何组织或个人因使用、分发或以其他方式利用本项目所造成的**一切后果**（包括但不限于法律诉讼、经济损失、数据泄露等），**均由使用者自行承担**。项目作者**不承担任何连带责任**。
4.  **无担保：** 本项目**不提供任何形式的担保**，包括但不限于**适销性、特定用途适用性或非侵权性**。
5.  **代码来源：** 本项目中所有逻辑和算法均为作者在理解公开机制后**独立编写**，**未复制或包含任何目标网站的原始、受保护的代码片段**。

**一旦您克隆或下载本项目，即视为您已同意并接受上述所有条款。**




## 许可证 (License)

本项目采用**MIT许可证**。




## 🛠️ 安装与使用 (Installation and Usage)

### 1. 创建 Session
```python
# 导入工厂方法
from request.web.xhs_session import create_xhs_session

# 配置代理(必须)
proxy = "http://127.0.0.1:7890"

# 方式1: 游客创建
xhs_session = await create_xhs_session(proxy=proxy)

# 方式2: 已有账号登录
xhs_session = await create_xhs_session(proxy=proxy, web_session="030037afxxxxxxxxxxxxxxxxxxxaeb59d5b4")

# 方式3: app sid 自动扫码登录 (需自行补充app协议, 位置在 request/web/apis/auth.py 48行 与 101行 附近)
xhs_session = await create_xhs_session(proxy=proxy, sid="179999999999999999999")

```

### 2. 调用 Session

#### 整体 Session 基于 `aiohttp` 所以使用起来需保证同样风格

```python
res = await xhs_session.apis.auth.get_self_simple_info()
logger.success("个人信息 | " + (await res.text()))

# 打印所有cookie
for a,b in xhs_session.cookies.items():
    logger.success(f'"{a}": "{b}", ')

res = await xhs_session.apis.note.note_detail("68add7d50xxxxxxxxxx37569", "ABFezCZFDcUHv-xxxxxxxxxxxHn4p5zH8=")
logger.success("笔记详情 | " + (await res.text()))

res = await xhs_session.apis.comments.get_comments("68add7d50xxxxxxxxxx37569", "ABFezCZFDcUHv-xxxxxxxxxxxHn4p5zH8=")
logger.success("笔记评论列表 | " + (await res.text()))

res = await xhs_session.apis.note.search_notes("口红")
logger.success("搜索笔记 | " + (await res.text()))

res = await xhs_session.apis.user.follow_user("5f86feee000000000101e3cb")
logger.success("关注 | " + (await res.text()))
```



### 3. 关闭 Session

```python
# 要记得关
await xhs_session.close_session()
```



### 4. 增加接口: 

- 在 `request/web/apis` 目录下选择所需接口类目对应添加即可， 增加模板如下:

  ```python
  # comments.py
  
  # post请求demo
  async def demo_post(self, test_demo: str) -> aiohttp.ClientResponse:
      url = "https://edith.xiaohongshu.com/api/test_demo"
      data = {
          'test_demo': test_demo
      }
      return await self.session.request(method="post", url=url, data=data)
  
  # get请求demo
  async def demo_get(self, test_demo: str) -> aiohttp.ClientResponse:
      url = "https://edith.xiaohongshu.com/api/test_demo"
      params = {
          'test_demo': test_demo
      }
      return await self.session.request(method="get", url=url, params=params)
  ```

  然后就可以使用了

  ```python
  res = await xhs_session.apis.comments.demo_post("test_demo")
  logger.success("demo_post | " + (await res.text()))
  
  res = await xhs_session.apis.comments.demo_get("test_demo")
  logger.success("demo_get | " + (await res.text()))
  ```

  

- 如果需要增加类目文件，则需要在 `__init__.py` 中 更改如下代码:

  ```python
  # __init__.py
  
  class APIModule:
      def __init__(self, __session):
          self.auth = Authentication(__session)
          self.comments = Comments(__session)
          self.note = Note(__session)
          self.user = User(__session)
          
          # 新增
          self.new = New(__session)
  ```

  同时新建new.py文件，并增加如下内容:

  ```python
  # new.py
  import aiohttp
  
  from typing import TYPE_CHECKING
  if TYPE_CHECKING:
      from request.web.xhs_session import XHS_Session  # 仅类型检查时导入
      
  class New:
      def __init__(self, session: "XHS_Session"):
          self.session = session  # 保存会话引用
          
    	# TODO STH...
  ```





### 5. 其他

- 配置文件在 `request/web/encrypt/web_encrypt_config.ini`

  - 小版本号修改配置文件中内含完整说明

  - 加密配置有能力自行修改



### 6. 请我喝个咖啡吧

![](https://github.com/Cialle/RedCrack/blob/master/imgs/alipay.jpg?raw=true)
![](https://github.com/Cialle/RedCrack/blob/master/imgs/wechat.jpg?raw=true)


## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Cialle/RedCrack&type=date&legend=top-left)](https://www.star-history.com/#Cialle/RedCrack&type=date&legend=top-left)
