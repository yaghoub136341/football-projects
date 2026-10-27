# -*- coding: utf-8 -*-
"""اجرای برنامهٔ جدول لیگ برتر ایران — نسخهٔ گرافیکی ویندوزی (RTL)"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    try:
        import customtkinter  # noqa: F401
    except ImportError:
        print("برای اجرای رابط گرافیکی، کتابخانهٔ customtkinter لازم است:")
        print("   pip install customtkinter pillow")
        sys.exit(1)
    from lig.app import LeagueApp
    app = LeagueApp()
    app.mainloop()


if __name__ == "__main__":
    main()
