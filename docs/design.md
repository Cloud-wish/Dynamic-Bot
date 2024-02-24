# 整体框架
- [adapters](https://github.com/Cloud-wish/Dynamic-Bot/blob/main/bot/adapters): 对接各种Bot框架，实现消息收发
- [commands](https://github.com/Cloud-wish/Dynamic-Bot/blob/main/bot/commands)：处理接收到的指令并返回结果
- [tasks](https://github.com/Cloud-wish/Dynamic-Bot/blob/main/bot/tasks)：需要持续运行的协程（例如：从Crawler接收消息推送）
- [handlers](https://github.com/Cloud-wish/Dynamic-Bot/blob/main/bot/handlers)：需要推送的消息处理器
- [builders](https://github.com/Cloud-wish/Dynamic-Bot/blob/main/bot/builders)：将收到的推送消息构建为实际的推送消息
# 功能扩展
- 除了[builders](https://github.com/Cloud-wish/Dynamic-Bot/blob/main/bot/builders)以外的以上4类，只需要在对应文件夹下新建代码文件，导入`init.py`中的`get_{type}_table`函数获取到`{type}_tables`，并在实际处理的协程前添加注解`@{type}_tables.{type}()`即可自动导入，并在满足设定的条件时执行。不同类型的注解中可使用的参数不同，可参考各类型下`init.py`中的具体实现。

  示例:
  ```python
  from ..utils.model import Message
  from .init import get_command_table

  command_table = get_command_table()

  @command_table.cmd("my_custom_command") # command支持多指令, 正则表达式匹配, 预设参数
  async def my_custom_command(cmd: str, msg: Message):
      ...
  ```
- [builders](https://github.com/Cloud-wish/Dynamic-Bot/blob/main/bot/builders)不会被自动导入，需要[handlers](https://github.com/Cloud-wish/Dynamic-Bot/blob/main/bot/handlers)中的消息处理器手动调用。

# 数据流
- 指令处理数据流：
  - adapter接收到消息，转换为Message格式
  - dispatch_msg将指令分发给对应的command
  - command进行命令处理，并将结果消息发送到消息队列
  - send_msg从消息队列中取出消息，进行消息发送
- 推送消息数据流：
  - receive_push从crawler接收，转交给dispatch_push
  - dispatch_push将消息分发给对应推送类型的handler
  - handler调用builder构建实际的推送消息，并发送到消息队列
  - send_msg从消息队列中取出消息，进行消息发送