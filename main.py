from kivy.app import App
from kivy.core.window import Window
from game_logic import Game

class MiniGameApp(App):
    def build(self):
        Window.size = (480, 800)  # 竖屏
        return Game()             # Game() 由 game_logic.py 提供

if __name__ == "__main__":
    MiniGameApp().run()
