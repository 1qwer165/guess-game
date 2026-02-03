from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.gridlayout import GridLayout
from kivy.uix.modalview import ModalView
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Line, RoundedRectangle
from kivy.core.audio import SoundLoader
from kivy.properties import StringProperty, NumericProperty, OptionProperty
import json
import os
import random

# ==================== 环境配置 ====================
try:
    from plyer import accelerometer
except ImportError:
    accelerometer = None

Config.set('graphics', 'width', '900')
Config.set('graphics', 'height', '500')
Window.clearcolor = (1, 1, 1, 1)

CHINESE_FONT = 'fonts/SourceHanSansSC-Regular.otf'
if not os.path.exists(CHINESE_FONT):
    print(f"警告: 字体文件 {CHINESE_FONT} 不存在！将在手机上使用默认字体。")
    CHINESE_FONT = None


# ==================== 通用 UI 组件 ====================
class RoundedButton(Button):
    """通用圆角按钮"""

    def __init__(self, bg_color=(0.2, 0.6, 1, 1), radius=[20, ], **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0, 0, 0, 0)
        self.bg_color_value = bg_color
        self.radius_value = radius

        with self.canvas.before:
            Color(*self.bg_color_value)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=self.radius_value)
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size


class MenuItem(ButtonBehavior, BoxLayout):
    """'我的'界面列表项"""

    def __init__(self, text, callback, color=(0.25, 0.25, 0.3, 1), **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 80
        self.padding = [20, 0, 20, 0]
        self.callback = callback

        with self.canvas.before:
            Color(*color)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[10, ])
        self.bind(pos=self.update_rect, size=self.update_rect)

        lbl = Label(text=text, font_size=24, halign='left', valign='middle', text_size=(self.width, None),
                    font_name=CHINESE_FONT if CHINESE_FONT else 'Roboto')
        lbl.bind(size=lbl.setter('text_size'))
        self.add_widget(lbl)

        arrow = Label(text=">", font_size=24, size_hint_x=None, width=50, color=(0.6, 0.6, 0.6, 1))
        self.add_widget(arrow)

    def update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def on_release(self):
        if self.callback: self.callback()


class SettingsPopup(ModalView):
    """设置弹窗 (修改版：支持两种模式切换)"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.7, 0.7)
        self.background_color = (0, 0, 0, 0.5)
        self.app = App.get_running_app()

        with self.canvas.before:
            Color(0.2, 0.2, 0.25, 1)
            self.rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[20, ])
        self.bind(pos=self.update_rect, size=self.update_rect)

        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=20)

        # 标题
        title = Label(text="游戏模式设置", font_size=32, bold=True, size_hint=(1, 0.15),
                      font_name=CHINESE_FONT if CHINESE_FONT else 'Roboto')
        self.layout.add_widget(title)

        # === 模式切换按钮区 ===
        mode_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint=(1, 0.15))

        self.btn_mode_time = RoundedButton(text="倒计时模式", font_name=CHINESE_FONT)
        self.btn_mode_time.bind(on_press=lambda x: self.switch_mode('time'))

        self.btn_mode_score = RoundedButton(text="竞速模式", font_name=CHINESE_FONT)
        self.btn_mode_score.bind(on_press=lambda x: self.switch_mode('score'))

        mode_layout.add_widget(self.btn_mode_time)
        mode_layout.add_widget(self.btn_mode_score)
        self.layout.add_widget(mode_layout)

        # === 说明文字 ===
        self.desc_lbl = Label(text="", font_size=18, color=(0.8, 0.8, 0.8, 1), size_hint=(1, 0.1),
                              font_name=CHINESE_FONT)
        self.layout.add_widget(self.desc_lbl)

        # === 选项网格 (动态生成) ===
        self.options_grid = GridLayout(cols=2, spacing=15, size_hint=(1, 0.4))
        self.layout.add_widget(self.options_grid)

        # === 关闭按钮 ===
        close_btn = Button(text="保存并关闭", size_hint=(1, 0.2), background_normal='',
                           background_color=(0.4, 0.4, 0.4, 1),
                           font_name=CHINESE_FONT if CHINESE_FONT else 'Roboto')
        close_btn.bind(on_press=self.dismiss)
        self.layout.add_widget(close_btn)

        self.add_widget(self.layout)

        # 初始化显示当前状态
        self.switch_mode(self.app.game_mode)

    def update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def switch_mode(self, mode):
        """切换模式，更新UI"""
        self.app.game_mode = mode

        # 更新顶部按钮颜色状态
        if mode == 'time':
            self.btn_mode_time.bg_color_value = (0.2, 0.8, 0.2, 1)  # 选中绿
            self.btn_mode_score.bg_color_value = (0.3, 0.3, 0.4, 1)  # 未选灰
            self.desc_lbl.text = "在规定时间内，尽可能猜对更多题目"
            options = [30, 60, 90, 120]
            unit = "秒"
            current_val = self.app.target_value if self.app.target_value > 20 else 60
        else:
            self.btn_mode_time.bg_color_value = (0.3, 0.3, 0.4, 1)
            self.btn_mode_score.bg_color_value = (0.2, 0.8, 0.2, 1)
            self.desc_lbl.text = "猜对规定数量的题目，看谁用时最短"
            options = [5, 10, 15, 20]
            unit = "题"
            current_val = self.app.target_value if self.app.target_value <= 20 else 10

        # 刷新下方选项按钮
        self.options_grid.clear_widgets()
        for opt in options:
            is_selected = (opt == current_val)
            color = (0.9, 0.6, 0.2, 1) if is_selected else (0.3, 0.6, 1, 1)
            btn = RoundedButton(text=f"{opt}{unit}", bg_color=color, font_name=CHINESE_FONT)
            btn.bind(on_press=lambda x, val=opt: self.set_target(val, unit))
            self.options_grid.add_widget(btn)

    def set_target(self, value, unit):
        self.app.target_value = value
        # 刷新界面以显示选中状态
        self.switch_mode(self.app.game_mode)


# ==================== 1. 欢迎界面 ====================
class WelcomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.15, 0.15, 0.18, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)
        self.add_widget(
            Label(text='欢迎来到"你猜我划"！', font_size=50, font_name=CHINESE_FONT if CHINESE_FONT else 'Roboto'))
        Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'main_menu'), 1.5)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size


# ==================== 2. 主菜单界面 ====================
class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.15, 0.15, 0.18, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

        main_layout = BoxLayout(orientation='vertical', padding=[50, 60, 50, 60], spacing=20)

        title_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.4))
        title_layout.add_widget(
            Label(text='你猜我划', font_size=72, bold=True, font_name=CHINESE_FONT if CHINESE_FONT else 'Roboto'))
        title_layout.add_widget(Label(text='聚会破冰神器', font_size=24, color=(0.7, 0.7, 0.7, 1),
                                      font_name=CHINESE_FONT if CHINESE_FONT else 'Roboto'))

        btn_grid = GridLayout(cols=2, spacing=40, size_hint=(1, 0.6))
        btn_quiz = RoundedButton(text='题库', font_size=40, bg_color=(0.23, 0.53, 0.95, 1),
                                 font_name=CHINESE_FONT if CHINESE_FONT else 'Roboto')
        btn_quiz.bind(on_press=lambda x: setattr(self.manager, 'current', 'question_bank'))
        btn_my = RoundedButton(text='我的', font_size=40, bg_color=(0.95, 0.6, 0.2, 1),
                               font_name=CHINESE_FONT if CHINESE_FONT else 'Roboto')
        btn_my.bind(on_press=lambda x: setattr(self.manager, 'current', 'my_page'))

        btn_grid.add_widget(btn_quiz)
        btn_grid.add_widget(btn_my)
        main_layout.add_widget(title_layout)
        main_layout.add_widget(btn_grid)
        self.add_widget(main_layout)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size


# ==================== 3. 题库选择界面 ====================
class QuestionBankScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

        main_layout = BoxLayout(orientation='vertical', spacing=20, padding=30)
        self.grid = GridLayout(cols=2, spacing=20, padding=10, size_hint=(1, 0.8))
        self.quiz_data = self.load_data()
        self.create_buttons()

        back_btn = Button(text='返回', size_hint=(1, 0.1), background_color=(0.7, 0.2, 0.2, 1),
                          font_name=CHINESE_FONT if CHINESE_FONT else 'Roboto')
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main_menu'))

        main_layout.add_widget(Label(text='请选择题库类别', font_size=36, color=(0, 0, 0, 1), size_hint=(1, 0.1),
                                     font_name=CHINESE_FONT if CHINESE_FONT else 'Roboto'))
        main_layout.add_widget(self.grid)
        main_layout.add_widget(back_btn)
        self.add_widget(main_layout)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def load_data(self):
        try:
            if os.path.exists('words.json'):
                with open('words.json', 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {
            "动画类": ["千与千寻", "龙猫", "疯狂动物城", "你的名字"],
            "角色类": ["孙悟空", "哈利·波特", "蜘蛛侠", "钢铁侠"],
            "体育类": ["篮球", "足球", "乒乓球", "游泳"],
            "娱乐圈": ["电影", "电视剧", "综艺", "明星"],
            "成语类": ["画蛇添足", "守株待兔", "叶公好龙", "亡羊补牢"]
        }

    def create_buttons(self):
        self.grid.clear_widgets()
        for cat in self.quiz_data.keys():
            btn = Button(text=cat, font_size=28, color=(0, 0, 0, 1), background_color=(0.9, 0.9, 0.9, 1),
                         font_name=CHINESE_FONT if CHINESE_FONT else 'Roboto')
            btn.bind(on_press=lambda x, c=cat: self.select_category(c))
            self.grid.add_widget(btn)

    def select_category(self, category):
        game_screen = App.get_running_app().root.get_screen('game')
        game_screen.set_category(category, self.quiz_data[category])
        App.get_running_app().root.current = 'game'


# ==================== 4. "我的"界面 ====================
class MyPageScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.15, 0.15, 0.18, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

        main_layout = BoxLayout(orientation='vertical', spacing=20, padding=30)

        user_card = BoxLayout(orientation='horizontal', size_hint=(1, 0.25), padding=20, spacing=20)
        with user_card.canvas.before:
            Color(0.2, 0.5, 0.9, 0.8)
            self.user_rect = RoundedRectangle(size=user_card.size, pos=user_card.pos, radius=[15, ])
        user_card.bind(
            pos=lambda i, v: setattr(self.user_rect, 'pos', i.pos) or setattr(self.user_rect, 'size', i.size),
            size=lambda i, v: setattr(self.user_rect, 'pos', i.pos) or setattr(self.user_rect, 'size', i.size))

        user_card.add_widget(Label(text="头像", font_name=CHINESE_FONT if CHINESE_FONT else 'Roboto'))
        user_card.add_widget(
            Label(text="未登录用户", font_size=28, halign='left', font_name=CHINESE_FONT if CHINESE_FONT else 'Roboto'))

        menu_layout = BoxLayout(orientation='vertical', spacing=15, size_hint=(1, 0.6))
        menu_layout.add_widget(MenuItem("历史记录", lambda: print("历史")))
        menu_layout.add_widget(MenuItem("清空缓存", lambda: print("清空")))
        menu_layout.add_widget(MenuItem("游戏设置", lambda: SettingsPopup().open()))
        menu_layout.add_widget(Label())

        back_btn = Button(text="返回主菜单", size_hint=(1, 0.15), background_color=(0.3, 0.3, 0.3, 1),
                          font_name=CHINESE_FONT if CHINESE_FONT else 'Roboto')
        back_btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'main_menu'))

        main_layout.add_widget(user_card)
        main_layout.add_widget(menu_layout)
        main_layout.add_widget(back_btn)
        self.add_widget(main_layout)

    def _update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size


# ==================== 5. 游戏界面 (支持两种模式) ====================
class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.questions = []
        self.score = 0
        self.timer_val = 0  # 记录时间 (剩余时间 或 已用时间)
        self.timer_event = None
        self.sensor_event = None
        self.is_cooldown = False
        self.app = App.get_running_app()

        try:
            self.snd_correct = SoundLoader.load('audio/correct.wav')
            self.snd_wrong = SoundLoader.load('audio/wrong.wav')
        except:
            self.snd_correct = None
            self.snd_wrong = None

        main_layout = BoxLayout(orientation='vertical', spacing=10, padding=30)

        # 顶部提示栏 (显示倒计时 或 目标进度)
        self.timer_lbl = Label(
            text="",
            font_size=40,
            color=(1, 0, 0, 1),
            size_hint=(1, 0.1),
            bold=True,
            font_name=CHINESE_FONT if CHINESE_FONT else 'Roboto'
        )
        main_layout.add_widget(self.timer_lbl)

        self.q_container = BoxLayout(orientation='vertical', size_hint=(1, 0.6))
        with self.q_container.canvas.before:
            Color(0, 0, 0, 1)
            self.border = Line(width=2)
        self.q_container.bind(pos=self._update_border, size=self._update_border)

        self.q_lbl = Label(text="准备...", font_size=60, color=(0, 0, 0, 1),
                           font_name=CHINESE_FONT if CHINESE_FONT else 'Roboto')
        self.q_container.add_widget(self.q_lbl)
        main_layout.add_widget(self.q_container)

        btn_layout = BoxLayout(spacing=40, size_hint=(1, 0.3))

        self.wrong_btn = Button(text="跳过", font_size=36, color=(0, 0, 0, 1), background_color=(0, 0, 0, 0),
                                font_name=CHINESE_FONT if CHINESE_FONT else 'Roboto')
        with self.wrong_btn.canvas.before:
            Color(0, 0, 0, 1)
            self.w_border = Line(rounded_rectangle=(0, 0, 1, 1, 10), width=1.5)
        self.wrong_btn.bind(
            pos=lambda i, v: setattr(self.w_border, 'rounded_rectangle', (i.x, i.y, i.width, i.height, 10)),
            size=lambda i, v: setattr(self.w_border, 'rounded_rectangle', (i.x, i.y, i.width, i.height, 10)))
        self.wrong_btn.bind(on_press=self.handle_wrong)

        self.right_btn = Button(text="正确", font_size=36, color=(0, 0, 0, 1), background_color=(0, 0, 0, 0),
                                font_name=CHINESE_FONT if CHINESE_FONT else 'Roboto')
        with self.right_btn.canvas.before:
            Color(0, 0, 0, 1)
            self.r_border = Line(rounded_rectangle=(0, 0, 1, 1, 10), width=1.5)
        self.right_btn.bind(
            pos=lambda i, v: setattr(self.r_border, 'rounded_rectangle', (i.x, i.y, i.width, i.height, 10)),
            size=lambda i, v: setattr(self.r_border, 'rounded_rectangle', (i.x, i.y, i.width, i.height, 10)))
        self.right_btn.bind(on_press=self.handle_correct)

        btn_layout.add_widget(self.wrong_btn)
        btn_layout.add_widget(self.right_btn)
        main_layout.add_widget(btn_layout)
        self.add_widget(main_layout)

    def _update_border(self, instance, value):
        self.border.rectangle = (instance.x, instance.y, instance.width, instance.height)

    def on_enter(self):
        self.start_sensor()

    def on_leave(self):
        self.stop_sensor();
        self.stop_timer()

    def set_category(self, name, questions):
        self.questions = questions.copy()
        random.shuffle(self.questions)
        self.score = 0
        self.current_index = 0
        self.wrong_btn.disabled = False
        self.right_btn.disabled = False

        # === 根据模式初始化 ===
        self.app = App.get_running_app()
        if self.app.game_mode == 'time':
            # 倒计时模式： timer_val 代表剩余时间
            self.timer_val = self.app.target_value
            self.update_display_text()
        else:
            # 竞速模式： timer_val 代表已经花的时间 (0开始加)
            self.timer_val = 0
            self.update_display_text()

        self.show_question()
        if self.timer_event: self.timer_event.cancel()
        self.timer_event = Clock.schedule_interval(self.update_time, 0.1)  # 0.1秒刷新一次更流畅

    def show_question(self):
        if self.current_index >= len(self.questions): random.shuffle(self.questions); self.current_index = 0
        self.q_lbl.text = self.questions[self.current_index]

    def update_time(self, dt):
        if self.app.game_mode == 'time':
            # 倒计时模式
            self.timer_val -= dt
            if self.timer_val <= 0:
                self.timer_val = 0
                self.game_over()
        else:
            # 竞速模式 (正向计时)
            self.timer_val += dt

        self.update_display_text()

    def update_display_text(self):
        """更新顶部状态栏文字"""
        if self.app.game_mode == 'time':
            # 显示：剩余 59.5 秒
            self.timer_lbl.text = f"{int(self.timer_val)}秒"
        else:
            # 显示：已答 3/10 题 (12.5秒)
            target = self.app.target_value
            self.timer_lbl.text = f"进度: {self.score}/{target}  ({self.timer_val:.1f}秒)"

    def stop_timer(self):
        if self.timer_event: self.timer_event.cancel(); self.timer_event = None

    def handle_correct(self, instance):
        if self.snd_correct and self.snd_correct.state != 'stop': self.snd_correct.stop()
        if self.snd_correct: self.snd_correct.play()

        self.score += 1
        self.current_index += 1

        # 竞速模式下，检查是否达标
        if self.app.game_mode == 'score' and self.score >= self.app.target_value:
            self.game_over()
            return

        self.show_question()

    def handle_wrong(self, instance):
        if self.snd_wrong and self.snd_wrong.state != 'stop': self.snd_wrong.stop()
        if self.snd_wrong: self.snd_wrong.play()

        self.current_index += 1
        self.show_question()

    def game_over(self):
        self.stop_timer()
        self.stop_sensor()
        self.wrong_btn.disabled = True
        self.right_btn.disabled = True

        if self.app.game_mode == 'time':
            msg = f"时间到!\n最终得分: {self.score}"
        else:
            msg = f"挑战成功!\n用时: {self.timer_val:.1f} 秒"

        self.q_lbl.text = msg
        Clock.schedule_once(lambda dt: setattr(self.manager, 'current', 'question_bank'), 4)

    def start_sensor(self):
        if accelerometer:
            try:
                accelerometer.enable();
                self.sensor_event = Clock.schedule_interval(self.check_tilt, 0.1)
            except:
                pass

    def stop_sensor(self):
        if self.sensor_event: self.sensor_event.cancel()
        if accelerometer:
            try:
                accelerometer.disable()
            except:
                pass

    def check_tilt(self, dt):
        if self.is_cooldown or self.wrong_btn.disabled: return
        try:
            val = accelerometer.acceleration
            if val and val[2]:
                if val[2] < -7:
                    self.handle_correct(None);
                    self.cooldown()
                elif val[2] > 7:
                    self.handle_wrong(None);
                    self.cooldown()
        except:
            pass

    def cooldown(self):
        self.is_cooldown = True
        Clock.schedule_once(lambda dt: setattr(self, 'is_cooldown', False), 1.5)


class GuessGameApp(App):
    # 定义全局变量 (模式 和 目标值)
    # game_mode: 'time' (倒计时) 或 'score' (竞速/题数)
    game_mode = StringProperty('time')
    # target_value: 如果是 time 模式，这里存的是秒数 (如 60)
    #               如果是 score 模式，这里存的是题数 (如 10)
    target_value = NumericProperty(60)

    def build(self):
        Window.set_title('你猜我划')
        sm = ScreenManager()
        sm.add_widget(WelcomeScreen(name='welcome'))
        sm.add_widget(MainMenuScreen(name='main_menu'))
        sm.add_widget(QuestionBankScreen(name='question_bank'))
        sm.add_widget(MyPageScreen(name='my_page'))
        sm.add_widget(GameScreen(name='game'))
        return sm


if __name__ == '__main__':
    GuessGameApp().run()
