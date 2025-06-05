"""
Flappy-Square – 改进完整版
─────────────────────────
• 点击 / 轻触：小方块上升；穿过一组管道 +1 分（左上角显示）。
• 撞管或落到褐色地面 → GAME OVER，显示分数，再点一下即可重新开始。
"""

import random
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.properties import NumericProperty, ListProperty
from kivy.clock import Clock
from kivy.graphics import Rectangle, Color
from kivy.core.audio import SoundLoader

# ───────────── 常量 ─────────────
GROUND_H      = 80          # 地面条高度
GRAVITY       = -900
JUMP_VELOC    = 350
PIPE_SPEED    = -220
PIPE_GAP      = 180
PIPE_INTERVAL = 1.4         # 秒

# ───────────── Bird ─────────────
class Bird(Widget):
    vel_y = NumericProperty(0)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.size = (40, 40)
        with self.canvas:
            self.rect = Rectangle(source='assets/square.png',
                                  pos=self.pos, size=self.size)
        self.bind(pos=self._sync_rect, size=self._sync_rect)

    def _sync_rect(self, *_):
        self.rect.pos, self.rect.size = self.pos, self.size

# ───────────── Pipe ─────────────
class Pipe(Widget):
    """上下两截管道，可见长度 = 碰撞长度"""
    passed = False

    def __init__(self, gap_y, **kw):
        super().__init__(**kw)
        self.width = 70
        self.gap_y = gap_y
        with self.canvas:
            self.rect_top = Rectangle(source='assets/pipe.png')
            self.rect_bot = Rectangle(source='assets/pipe.png')
        self.bind(pos=self._sync_rect, size=self._sync_rect)
        self._sync_rect()

    def _sync_rect(self, *_):
        gap_top = self.gap_y + PIPE_GAP / 2
        gap_bot = self.gap_y - PIPE_GAP / 2
        # 上管道
        self.rect_top.pos  = (self.x, gap_top)
        self.rect_top.size = (self.width, Window.height - gap_top)
        # 下管道
        self.rect_bot.pos  = (self.x, GROUND_H)
        self.rect_bot.size = (self.width, gap_bot - GROUND_H)

# ───────────── Game ─────────────
class Game(Widget):
    score = NumericProperty(0)
    pipes = ListProperty()

    def __init__(self, **kw):
        super().__init__(**kw)

        # 1) 画固定地面（只创建一次）
        with self.canvas.before:
            Color(.36, .28, .17)  # 褐色
            self.ground_rect = Rectangle(pos=(0, 0),
                                         size=(Window.width, GROUND_H))
        Window.bind(size=self._update_ground)

        # 2) 其余初始化
        Window.clearcolor = (.53, .79, .92, 1)      # 天空蓝
        self.started  = False
        self.gameover = False

        self.bird = Bird(pos=(Window.width * 0.3, Window.height * 0.6))
        self.add_widget(self.bird)

        # HUD
        self.score_lbl = Label(text="0", font_size=36,
                               # font_name="assets/fonts/PressStart2P.ttf",
                               pos=(20, Window.height - 60),
                               size_hint=(None, None), color=(1, 1, 1, 1))
        self.add_widget(self.score_lbl)

        self.sound = SoundLoader.load('assets/flap.wav')

        Clock.schedule_interval(self.update, 1 / 60)
        self.spawn_pipe(initial=True)

    # —— 地面随窗口宽度自适应 ——
    def _update_ground(self, *_):
        self.ground_rect.size = (Window.width, GROUND_H)

    # —— 触控：跳跃 / 重开 ——
    def on_touch_down(self, *_):
        if self.gameover:
            self.reset()
            return

        if not self.started:
            self.started = True
            Clock.schedule_interval(self.spawn_pipe, PIPE_INTERVAL)

        self.bird.vel_y = JUMP_VELOC
        if self.sound:
            self.sound.play()

    # —— 主循环 ——
    def update(self, dt):
        if not self.started or self.gameover:
            return

        # Bird 物理
        self.bird.vel_y += GRAVITY * dt
        ny = self.bird.y + self.bird.vel_y * dt
        self.bird.y = max(min(ny, Window.height - self.bird.height), 0)

        # 管道移动 / 碰撞
        for pipe in list(self.pipes):
            pipe.x += PIPE_SPEED * dt

            if pipe.x + pipe.width < 0:             # 离屏移除
                self.remove_widget(pipe)
                self.pipes.remove(pipe)
                continue

            if (not pipe.passed) and (pipe.x + pipe.width < self.bird.x):  # 加分
                self.score += 1
                self.score_lbl.text = str(self.score)
                pipe.passed = True

            # AABB 碰撞
            bx, by, bw, bh = self.bird.x, self.bird.y, *self.bird.size
            px, pw = pipe.x, pipe.width
            gap_top = pipe.gap_y + PIPE_GAP / 2
            gap_bot = pipe.gap_y - PIPE_GAP / 2
            hit = (bx < px + pw and bx + bw > px and
                   (by + bh > gap_top or by < gap_bot))
            if hit:
                self._end_game()
                return

        # 掉到地面
        if self.bird.y <= GROUND_H - 2:
            self._end_game()

    # —— 生成管道 ——
    def spawn_pipe(self, _=None, *, initial=False):
        gap_y = random.randint(int(Window.height * .35),
                               int(Window.height * .75))
        gap_y = round(gap_y / 4) * 4
        start_x = Window.width if not initial else Window.width * 1.3
        pipe = Pipe(gap_y, x=start_x, y=0)
        self.add_widget(pipe)
        self.pipes.append(pipe)

    # —— 游戏结束 ——
    def _end_game(self):
        Clock.unschedule(self.update)
        Clock.unschedule(self.spawn_pipe)
        self.gameover = True

        # 半透明幕布 + 文本
        with self.canvas.after:
            Color(0, 0, 0, .55)
            self.overlay = Rectangle(pos=(0, 0), size=Window.size)

        self.over_lbl = Label(text=f"GAME OVER\\nScore: {self.score}\\nTap to restart",
                              halign='center', valign='middle',
                              font_size=46, color=(1, 1, 1, 1),
                              size_hint=(None, None), size=Window.size)
        self.add_widget(self.over_lbl)

    # —— 复位而非重建 ——
    def reset(self):
        # 移除管道
        for p in list(self.pipes):
            self.remove_widget(p)
        self.pipes.clear()

        # 去掉 Game-Over UI
        if hasattr(self, 'over_lbl'):
            self.remove_widget(self.over_lbl)
        if hasattr(self, 'overlay'):
            self.canvas.after.remove(self.overlay)
            del self.overlay

        # 复位 Bird & 分数
        self.bird.pos  = (Window.width * 0.3, Window.height * 0.6)
        self.bird.vel_y = 0
        self.score = 0
        self.score_lbl.text = "0"

        # 恢复状态 & 重新调度
        self.started = False
        self.gameover = False
        Clock.schedule_interval(self.update, 1 / 60)
