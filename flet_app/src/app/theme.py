import flet as ft

BLACK = "#000000"
SURFACE = "#0A0A0A"
SURFACE_2 = "#141414"
SURFACE_3 = "#1E1E1E"
WHITE = "#FFFFFF"
GREEN = "#1DB954"
YELLOW = "#FFE346"
RED = "#FF2D55"
TEXT_2 = "#8C8C8C"
TEXT_3 = "#4A4A4A"
BORDER_DIM = "#2A2A2A"

PURPLE = "#8F87FF"
ORANGE = "#F7931E"
PINK = "#FF4D6D"
CYAN = "#00B4D8"
GOLD = "#F9C74F"
MINT = "#00F5D4"
LIME = "#B8F25C"
CORAL = "#FF8A3D"
SKY = "#5AC8FA"
VIOLET = "#C084FC"

FONT = "Mono"
FONT_BOLD = "MonoBold"

FONTS = {
    FONT: "fonts/SpaceMono-Regular.ttf",
    FONT_BOLD: "fonts/SpaceMono-Bold.ttf",
}

EASE = ft.AnimationCurve.EASE_OUT_CUBIC
EASE_SOFT = ft.AnimationCurve.EASE_OUT_QUART
SPRING = ft.AnimationCurve.EASE_OUT_BACK
ELASTIC = ft.AnimationCurve.ELASTIC_OUT

GUTTER = 20


def build_theme() -> ft.Theme:
    transition = ft.PageTransitionTheme.CUPERTINO
    return ft.Theme(
        font_family=FONT,
        color_scheme_seed=GREEN,
        color_scheme=ft.ColorScheme(
            primary=GREEN,
            on_primary=BLACK,
            secondary=YELLOW,
            surface=BLACK,
            on_surface=WHITE,
            error=RED,
        ),
        scaffold_bgcolor=BLACK,
        canvas_color=BLACK,
        splash_color=ft.Colors.TRANSPARENT,
        highlight_color=ft.Colors.TRANSPARENT,
        hover_color=ft.Colors.TRANSPARENT,
        page_transitions=ft.PageTransitionsTheme(
            android=transition,
            ios=transition,
            macos=transition,
            windows=transition,
            linux=transition,
        ),
        scrollbar_theme=ft.ScrollbarTheme(thickness=0),
        slider_theme=ft.SliderTheme(
            active_track_color=GREEN,
            inactive_track_color=SURFACE_3,
            thumb_color=WHITE,
            overlay_color=ft.Colors.with_opacity(0.15, GREEN),
            track_height=6,
        ),
        bottom_sheet_theme=ft.BottomSheetTheme(
            bgcolor=SURFACE,
            shape=ft.RoundedRectangleBorder(radius=0),
        ),
    )
