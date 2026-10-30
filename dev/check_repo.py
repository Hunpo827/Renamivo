import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from PySide6.QtWidgets import QApplication
from renamer import i18n, meta
from renamer.ui.dialogs import github_repo
from renamer.ui.theme import QSS
from renamer.ui.dialogs import AboutDialog
app = QApplication(sys.argv); app.setStyle("Fusion"); app.setStyleSheet(QSS)
i18n.set_language("zh")
print("repo =", github_repo())
print("home =", meta.GITHUB_HOME.format(repo=github_repo()))
print("latest =", meta.GITHUB_LATEST.format(repo=github_repo()))
d = AboutDialog()
print("buttons enabled:", d.btn_gh.isEnabled(), d.btn_update.isEnabled())
