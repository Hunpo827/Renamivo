"""应用元信息。发版时改这里。"""

APP_NAME = "易名匣"
APP_NAME_EN = "Renamivo"
APP_VERSION = "1.3.3"
APP_AUTHOR = ""

# GitHub 仓库（owner/repo）。留空则「关于」里的跳转会显示为未配置。
# 也可以在 %APPDATA%\BatchRenamer\config.json 里写 {"github_repo": "owner/repo"} 覆盖，
# 这样不用重新打包。
GITHUB_REPO = "Hunpo827/Renamivo"

GITHUB_HOME = "https://github.com/{repo}"
GITHUB_LATEST = "https://github.com/{repo}/releases/latest"


def app_display_name() -> str:
    """当前语言下的软件名：中文用「易名匣」，其他一律 Renamivo。"""
    from . import i18n
    return APP_NAME if i18n.current_language() == "zh" else APP_NAME_EN
