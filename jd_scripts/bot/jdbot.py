# -*- coding: utf-8 -*-
# @Author    : iouAkira(lof)
# @mail      : e.akimoto.akira@gmail.com
# @CreateTime: 2021-03-31
# @UpdateTime: 2021-03-31

import logging
import os
import re

import jdutils
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ChatType, ParseMode

# 日志输出格式配置
logging.basicConfig(format='%(asctime)s-%(name)s-%(levelname)s=> [%(funcName)s] %(message)s ', level=logging.INFO)
logger = logging.getLogger(__name__)

bot_token, chat_id, _EXT = "", "", ""
if 'EXT' in os.environ:
    _EXT = os.getenv('EXT')
if "TG_BOT_TOKEN" in os.environ:
    bot_token = os.getenv("TG_BOT_TOKEN")
if 'TG_USER_ID' in os.environ:
    chat_id = os.getenv('TG_USER_ID')

if bot_token == "" or chat_id == "":
    logging.info("未找到bot token或者chat id配置无法启动bot交互功能")
    exit()

bot = Bot(token=bot_token)
# bot = Bot(token=bot_token, proxy="http://127.0.0.1:7890")
dp = Dispatcher(bot)

# 启用日志
logging.basicConfig(format='%(asctime)s-%(name)s-%(levelname)s=> [%(funcName)s] %(message)s ', level=logging.INFO)
logger = logging.getLogger(__name__)

_base_dir = '/scripts'
# _base_dir = '/Users/akira/jd_scripts'
_logs_dir = f'{_base_dir}/logs'
_docker_dir = f'{_base_dir}/docker'
_bot_dir = f'{_docker_dir}bot/'
_gen_code_conf = f'{_logs_dir}/code_gen_conf.list'
_crontabs_root = '/var/spool/cron/crontabs/root'

_interactive_cmd_list = ['node', 'spnode', 'crontab']
_gen_code_cmd_list = ['gen_long_code', 'gen_temp_code', 'gen_daily_code', _EXT]
_sys_cmd_list = ['ps', 'ls', 'wget', 'cat', 'echo', 'sed', 'restart']


@dp.message_handler(commands=['start', 'help'], chat_type=[ChatType.PRIVATE], chat_id=[chat_id])
async def help_handler(message: types.Message):
    # logger.info(message)
    spnode_readme = ""
    gen_cmd_list = _gen_code_cmd_list
    gen_cmd_list.remove('glc')
    if "DISABLE_SPNODE" not in os.environ:
        spnode_readme = "/spnode `获取可执行脚本的列表，选择对应的按钮执行。(拓展使用：运行指定路径脚本，例：/spnode /scripts/jd_818.js)`\n\n" \
                        "```" \
                        "使用bot交互+spnode后 后续用户的cookie维护更新只需要更新logs/cookies.list即可\n" \
                        "使用bot交互+spnode后 后续执行脚本命令请使用spnode否者无法使用logs/cookies.list的cookies执行脚本，定时任务也将自动替换为spnode命令执行\n" \
                        "spnode功能概述示例\n" \
                        "spnode conc /scripts/jd_bean_change.js \n >>>为每个cookie单独执行jd_bean_change脚本（伪并发\n" \
                        "spnode 1 /scripts/jd_bean_change.js \n >>>为logs/cookies.list文件里面第一行cookie账户单独执行jd_bean_change脚本\n" \
                        "spnode jd_XXXX /scripts/jd_bean_change.js \n >>>为logs/cookies.list文件里面pt_pin=jd_XXXX的cookie账户单独执行jd_bean_change脚本\n" \
                        "spnode /scripts/jd_bean_change.js \n >>>为logs/cookies.list所有cookies账户一起执行jd_bean_change脚本\n" \
                        "请仔细阅读并理解上面的内容，使用bot交互默认开启spnode指令功能功能。\n" \
                        "如需___停用___请配置环境变量 -DISABLE_SPNODE=True" \
                        "```"
    await bot.send_message(chat_id=message.from_user.id,
                           text="`限制自己使用的交互拓展机器人`\n" \
                                "\n" \
                                f"支持的的指令列表为：/{'| /'.join(_interactive_cmd_list)} \n"
                                f"/{'| /'.join(gen_cmd_list)}\n"
                                f"/{'| /'.join(_sys_cmd_list)} " \
                                f"{spnode_readme}",
                           parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(commands=_interactive_cmd_list, chat_type=[ChatType.PRIVATE], chat_id=[chat_id])
async def interactive_handler(message: types.Message):
    # logger.info(message)
    interactive_cmd = message.text.lstrip("/").split()
    scripts_file_path = _base_dir
    if len(interactive_cmd) > 1 and interactive_cmd[0].endswith("node"):
        done_msg = await bot.send_message(chat_id=message.from_user.id,
                                          text=f'➡️ {" ".join(interactive_cmd)} `正在执行中，请稍等`'.replace("_", "\_"),
                                          parse_mode=types.ParseMode.MARKDOWN)
        is_long, result = await jdutils.exec_script(command=" ".join(interactive_cmd), log_dir=_logs_dir)
        if is_long:
            await done_msg.delete()
            await bot.send_document(chat_id=message.from_user.id,
                                    document=open(result, 'rb'),
                                    caption=f'⬆️ {" ".join(interactive_cmd)}️ `执行结果超长，请查看日志` ⬆️'.replace("_", "\_"),
                                    parse_mode=types.ParseMode.MARKDOWN)
        else:
            await done_msg.edit_text(
                text=f'⬇️ {" ".join(interactive_cmd)} `执行结果` ⬇️\n\n'.replace("_", "\_") + f'```{result}```',
                parse_mode=types.ParseMode.MARKDOWN)

    else:
        if interactive_cmd[0] == 'crontab':
            scripts_file_path = _crontabs_root
        keyboard_markup = await jdutils.gen_reply_markup_btn(interactive_cmd=interactive_cmd[0],
                                                             scripts_file_path=scripts_file_path,
                                                             row_btn_cnt=2)
        keyboard_markup.add(types.InlineKeyboardButton(text="取消", callback_data="cancel"))
        await bot.send_message(chat_id=message.from_user.id,
                               text=f"⬇️⬇️ `请选择` {interactive_cmd[0]}` 需要执行的任务/脚本`",
                               reply_markup=keyboard_markup,
                               parse_mode=ParseMode.MARKDOWN)


@dp.message_handler(commands=_gen_code_cmd_list, chat_type=[ChatType.PRIVATE], chat_id=[chat_id])
async def gen_code_handler(message: types.Message):
    # logger.info(message)
    gen_code_cmd = message.text.lstrip("/").split()
    if gen_code_cmd[0] == 'glc':
        tk, okl_tk, ccc, glcimg = jdutils.get_glc()
        chk_msg = await bot.send_photo(chat_id=message.from_user.id,
                                       photo=open(glcimg, 'rb'),
                                       caption="⬆️ `Scan this QRCode` ⬆️",
                                       parse_mode=ParseMode.MARKDOWN)
        ec, result = await jdutils.chk_glc(tk, okl_tk, ccc)
        await chk_msg.delete()
        if ec == 0:
            succ_msg = await bot.send_message(chat_id=message.from_user.id,
                                              text=f"⬇️️ `Scan success` ⬇️" + "\n\n" + f"```{result}```",
                                              parse_mode=ParseMode.MARKDOWN)
            if len(gen_code_cmd) > 1:
                if gen_code_cmd[1] == '-tw':
                    test_msg = await succ_msg.reply(text="➡️➡️ `will be test new ccc to exec bean change.`",
                                                    parse_mode=ParseMode.MARKDOWN)
                    is_long, result = await jdutils.exec_script(log_dir=_logs_dir,
                                                                command=f'spnode {re.findall(r"in=(.+?);", result)[0]} {_base_dir}/jd_bean_change')
                    if is_long:
                        await test_msg.delete()
                        await succ_msg.reply_document(document=open(result, 'rb'),
                                                      caption=f'⬆️ `测试执行结果超长，请查看日志` ⬆️',
                                                      parse_mode=types.ParseMode.MARKDOWN)
                    else:
                        await test_msg.edit_text(text=f'⬇️ `测试执行结果` ⬇️\n\n' + f'```{result}```',
                                                 parse_mode=types.ParseMode.MARKDOWN)
        else:
            await bot.send_message(chat_id=message.from_user.id,
                                   text=f"➡️ ```{result}``` ⬅️️",
                                   parse_mode=ParseMode.MARKDOWN)
    else:
        msg_list = jdutils.gen_code_msg_list(gen_code_cmd=' '.join(gen_code_cmd), gen_code_conf=_gen_code_conf)
        for msg in msg_list:
            await bot.send_message(chat_id=message.from_user.id, text=msg)


@dp.message_handler(commands=_sys_cmd_list,
                    chat_type=[ChatType.PRIVATE],
                    chat_id=[chat_id])
async def sys_cmd_handler(message: types.Message):
    cmd_split = message.text.strip('/').split()
    done_msg_text = '`%s` 正在执行中' % (' '.join(cmd_split))
    if cmd_split[0] == "restart":
        try:
            await message.delete()
        except Exception as e:
            pass
        cmd_split = ['sh', f'{_base_dir}/logs/bot/jdbot.sh', 'restart_bot', '>>/dev/null 2>&1 &']
        done_msg_text = "➡️ `jd bot重启指令已发送...`"

    done_msg = await bot.send_message(chat_id=message.from_user.id,
                                      text=done_msg_text,
                                      parse_mode=types.ParseMode.MARKDOWN)
    is_long, result = await jdutils.exec_sys_cmd(sh_cmd=' '.join(cmd_split),
                                                 log_dir=_base_dir)
    if is_long:
        await done_msg.delete()
        await bot.send_document(chat_id=message.from_user.id,
                                document=open(result, 'rb'),
                                caption=f'⬆️ {" ".join(cmd_split)} `执行结果超长,请查看log` ⬆️' % (' '.join(cmd_split)),
                                parse_mode=types.ParseMode.MARKDOWN_V2)
    else:
        await done_msg.edit_text(
            text=f'⬇️ {" ".join(cmd_split)} `执行结果` ⬇️\n\n```{result}```',
            parse_mode=types.ParseMode.MARKDOWN)


async def query_callback_filter(query: types.CallbackQuery):
    callback_data = query.data.split()
    return {"callback_type": callback_data[0], 'data': ' '.join(callback_data[1:])}


@dp.callback_query_handler(query_callback_filter)
async def inline_kb_answer_callback_handler(query: types.CallbackQuery, callback_type: str, data: str):
    await query.answer(query.data)
    if callback_type == "cancel":
        await query.message.edit_text(
            text='➡️ `操作已取消` ⬅️',
            parse_mode=types.ParseMode.MARKDOWN_V2)
    else:
        command = query.data
        if callback_type == 'crontab':
            logger.info(data)
            command = data
        await query.message.edit_text(text=f'➡️ {command} `正在执行中，请稍等`'.replace("_", "\_"),
                                      parse_mode=types.ParseMode.MARKDOWN)
        is_long, result = await jdutils.exec_script(command=command, log_dir=_logs_dir)
        if is_long:
            await query.message.delete()
            await bot.send_document(chat_id=query.from_user.id,
                                    document=open(result, 'rb'),
                                    caption=f'⬆️ {command}️ `执行结果超长，请查看日志` ⬆️'.replace("_", "\_"),
                                    parse_mode=types.ParseMode.MARKDOWN)
        else:
            await query.message.edit_text(
                text=f'⬇️ {command} `执行结果` ⬇️\n\n'.replace("_", "\_") + f'```{result}```',
                parse_mode=types.ParseMode.MARKDOWN)


def main():
    executor.start_polling(dp, skip_updates=True)


# 生成依赖安装列表
# pip3 freeze > requirements.txt
# 或者使用pipreqs
# pip3 install pipreqs
# 在当前目录生成
# pipreqs . --encoding=utf8 --force
# 使用requirements.txt安装依赖
# pip3 install -r requirements.txt
if __name__ == '__main__':
    main()