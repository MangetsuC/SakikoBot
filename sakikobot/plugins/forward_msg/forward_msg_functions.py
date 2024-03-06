from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11.message import MessageSegment as onebot11_MessageSegment

def messageSegment_to_dict(msg_seg: onebot11_MessageSegment) -> dict:
    return dict(type = msg_seg.type, data = msg_seg.data)

def build_forward_msg(msg: list[onebot11_MessageSegment]) -> list[dict]:
    msg_list: list[dict] = []
    for i in msg:
        msg_list.append(dict(type = 'node', data = dict(content = [messageSegment_to_dict(i)])))
    return msg_list

async def send_private_forward_msg(bot: Bot, user_id: int, msg: list[onebot11_MessageSegment]) -> None:
    await bot.call_api('send_private_forward_msg', user_id = user_id, messages = build_forward_msg(msg))

async def send_group_forward_msg(bot: Bot, group_id: int, msg: list[onebot11_MessageSegment]) -> None:
    await bot.call_api('send_group_forward_msg', group_id = group_id, messages = build_forward_msg(msg))

async def send_forward_msg(bot: Bot, msg: list[onebot11_MessageSegment], user_id: int = 0, group_id: int = 0) -> None:
    if user_id:
        await send_private_forward_msg(bot, user_id, msg)
    elif group_id:
        await send_group_forward_msg(bot, group_id, msg)
    else:
        raise ValueError('No message target!')






