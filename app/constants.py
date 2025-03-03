from zoneinfo import ZoneInfo
from tzlocal import get_localzone


UTC = ZoneInfo('UTC')
DEFAULT_TIMEZONE = ZoneInfo(str(get_localzone()))
