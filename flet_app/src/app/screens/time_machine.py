import flet as ft

from app.api import ApiError
from app.screens.registry import number_of
from app.theme import BLACK, BORDER_DIM, CYAN, GOLD, GREEN, MINT, ORANGE, PINK, PURPLE, SPRING, SURFACE, TEXT_2, WHITE, YELLOW
from app.ui.result import ResultSlot
from app.ui.screen import Screen, header
from app.ui.widgets import BrutalButton, CountPicker, border, hard_shadow, label, txt

DECADES = [
    (1950, "Rock'n'roll and crooners", PINK),
    (1960, "British invasion, Motown", ORANGE),
    (1970, "Disco, punk, prog", GOLD),
    (1980, "Synths and big hair", PURPLE),
    (1990, "Grunge, rave, golden-era rap", CYAN),
    (2000, "Pop punk, R&B, indie sleaze", MINT),
    (2010, "EDM and the streaming era", GREEN),
    (2020, "Hyperpop and short-form chaos", YELLOW),
]


def color_of(decade: int) -> str:
    return next(c for d, _, c in DECADES if d == decade)


def build(app, feature, **_) -> ft.View:
    state = {"decade": 1980}
    result = ResultSlot()
    big = txt("80s", size=112, bold=True, color=PURPLE, height=0.9)
    big_box = ft.Container(
        big,
        scale=1,
        rotate=ft.Rotate(-0.04),
        animate_scale=ft.Animation(520, SPRING),
        animate_rotation=ft.Animation(620, SPRING),
    )
    caption = txt("Synths and big hair", size=13, color=TEXT_2)
    count = CountPicker("Tracks to queue", 10, 1, 50, accent=PURPLE, haptic=app.select)
    chips: dict[int, ft.Container] = {}

    def paint():
        for decade, chip in chips.items():
            on = decade == state["decade"]
            chip.bgcolor = color_of(decade) if on else SURFACE
            chip.content.color = BLACK if on else WHITE
            chip.border = border(BLACK if on else BORDER_DIM)
            chip.shadow = hard_shadow(WHITE, 3) if on else None
            chip.offset = ft.Offset(0, -0.12) if on else ft.Offset(0, 0)

    def pick(decade: int):
        if decade == state["decade"]:
            return
        app.select()
        state["decade"] = decade
        color = color_of(decade)
        big.value = f"{str(decade)[2:]}s"
        big.color = color
        caption.value = next(b for d, b, _ in DECADES if d == decade)
        big_box.scale = 0.6
        big_box.rotate = ft.Rotate(0.1 if (decade // 10) % 2 else -0.1)
        count.recolor(color)
        button.face.bgcolor = color
        paint()
        view.update()
        big_box.scale = 1
        big_box.rotate = ft.Rotate(-0.04)
        big_box.update()

    for decade, _, _ in DECADES:
        chips[decade] = ft.Container(
            txt(f"'{str(decade)[2:]}", size=16, bold=True),
            width=62,
            height=52,
            alignment=ft.Alignment.CENTER,
            animate=ft.Animation(220),
            animate_offset=ft.Animation(320, SPRING),
            on_click=lambda e, d=decade: pick(d),
        )
    paint()
    strip = ft.Container(
        ft.Row(list(chips.values()), spacing=10, scroll=ft.ScrollMode.HIDDEN),
        padding=ft.Padding.only(top=8, bottom=4, right=4),
    )

    async def submit(e):
        button.set_busy(True)
        try:
            data = await app.api.time_machine(state["decade"], count.value)
        except ApiError as exc:
            app.toast(exc.message, "error")
            return
        finally:
            button.set_busy(False)
        result.show(
            app,
            "Time travel complete",
            f"Welcome to the {big.value}",
            "Tracks landed in your queue.",
            color_of(state["decade"]),
            None,
            [("queued", str(data.get("added", 0))), ("missed", str(data.get("errors", 0)))],
            tracks=data.get("tracks"),
            total=data.get("added"),
        )
        await app.player.refresh()

    button = BrutalButton("Travel", ft.Icons.TRAVEL_EXPLORE, submit, accent=PURPLE, haptic=app.thud)
    view = Screen(
        app,
        "/time-machine",
        [
            *header(app, feature.title, "Pick an era and we will smuggle its hits straight into your queue.", feature.accent, feature.icon, number_of(feature.key)),
            ft.Column([label("Destination"), strip], spacing=6),
            ft.Column([big_box, caption], spacing=4),
            count,
            button,
            result,
        ],
        accent=feature.accent,
    )
    return view
