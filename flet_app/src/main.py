import flet as ft

from app.api import ApiError
from app.core import App
from app.screens.login import splash_view
from app.theme import BLACK, FONTS, build_theme


async def main(page: ft.Page):
    page.title = "MultiSpot"
    page.bgcolor = BLACK
    page.padding = 0
    page.fonts = FONTS
    page.theme = build_theme()
    page.dark_theme = build_theme()
    page.theme_mode = ft.ThemeMode.DARK
    if not page.web and page.platform in (ft.PagePlatform.WINDOWS, ft.PagePlatform.MACOS, ft.PagePlatform.LINUX):
        page.window.width = 412
        page.window.height = 892
        page.window.resizable = True
    app = App(page)
    page.on_view_pop = app.on_view_pop
    page.on_app_lifecycle_state_change = lambda e: app.player.suspend(
        e.state in (ft.AppLifecycleState.PAUSE, ft.AppLifecycleState.HIDE, ft.AppLifecycleState.INACTIVE)
    )
    page.views.clear()
    page.views.append(splash_view())
    page.update()
    await app.boot()
    if app.api.session:
        try:
            app.user = await app.api.me()
        except ApiError:
            app.user = None
    if app.user:
        app.show_home()
    else:
        app.show_login()


if __name__ == "__main__":
    ft.run(main)
