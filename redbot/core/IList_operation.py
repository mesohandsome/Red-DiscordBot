import asyncio
import contextlib
import datetime
import importlib
import itertools
import keyword
import logging
import io
import random
import markdown
import os
import re
import sys
import platform
import psutil
import getpass
import pip
import traceback
from pathlib import Path
from redbot.core import data_manager
from redbot.core.utils.menus import menu
from redbot.core.utils.views import SetApiView
from redbot.core.commands import GuildConverter, RawUserIdConverter
from string import ascii_letters, digits
from typing import (
    TYPE_CHECKING,
    Union,
    Tuple,
    List,
    Optional,
    Iterable,
    Sequence,
    Dict,
    Set,
    Literal,
)
import list_operations
import aiohttp
import discord
from babel import Locale as BabelLocale, UnknownLocaleError
from redbot.core.data_manager import storage_type

from . import (
    __version__,
    version_info as red_version_info,
    checks,
    commands,
    errors,
    i18n,
    bank,
    modlog,
)
from ._diagnoser import IssueDiagnoser
from .utils import AsyncIter, can_user_send_messages_in
from .utils._internal_utils import fetch_latest_red_version_info
from .utils.predicates import MessagePredicate
from .utils.chat_formatting import (
    box,
    escape,
    humanize_list,
    humanize_number,
    humanize_timedelta,
    inline,
    pagify,
)
from .commands import CommandConverter, CogConverter
from .commands.requires import PrivilegeLevel
from .commands.help import HelpMenuSetting

_entities = {
    "*": "&midast;",
    "\\": "&bsol;",
    "`": "&grave;",
    "!": "&excl;",
    "{": "&lcub;",
    "[": "&lsqb;",
    "_": "&UnderBar;",
    "(": "&lpar;",
    "#": "&num;",
    ".": "&period;",
    "+": "&plus;",
    "}": "&rcub;",
    "]": "&rsqb;",
    ")": "&rpar;",
}

_ = i18n.Translator("Core", __file__)

TokenConverter = commands.get_dict_converter(delims=[" ", ",", ";"])

MAX_PREFIX_LENGTH = 25

class IList_operation:
    async def process(self, add_or_rm, ctx: commands.Context, *users_or_roles: Union[discord.Member, discord.Role, int]):
        pass