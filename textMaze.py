import os
import random
import time
import pickle
import sys
import platform

# 跨平台输入处理
if platform.system() == 'Windows':
    from msvcrt import getch
else:
    import tty
    import termios

    def getch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

class SoundManager:
    """纯蜂鸣音效系统"""
    def __init__(self):
        self._init_beep()
        self.enabled = True

    def _init_beep(self):
        """初始化蜂鸣功能"""
        if platform.system() == 'Windows':
            import winsound
            self.beep = winsound.Beep
        else:
            # Linux/Mac使用系统铃声
            self.beep = self._unix_beep

    def _unix_beep(self, freq, duration):
        """Unix系统蜂鸣实现"""
        try:
            # 尝试通过脉冲音频发声
            os.system(f'play -nq synth {duration/1000} sine {freq} &> /dev/null &')
        except:
            # 使用终端默认铃声
            sys.stdout.write('\a')
            sys.stdout.flush()

    def play(self, sound_type):
        """播放蜂鸣音效"""
        if not self.enabled:
            return
        
        freq_duration = {
            'move': (2000, 80),   # 高频短音
            'wall': (500, 200),   # 低频长音
            'win': [(800,200), (1200,200), (1600,300)]  # 胜利旋律
        }

        sequence = freq_duration.get(sound_type, (500, 100))
        if isinstance(sequence[0], tuple):
            for f, d in sequence:
                self._play_single(f, d)
        else:
            self._play_single(*sequence)

    def _play_single(self, freq, duration):
        """播放单音"""
        try:
            if platform.system() == 'Windows':
                self.beep(freq, duration)
            else:
                self.beep(freq, duration)
        except Exception as e:
            self.enabled = False

import collections

class MazeGenerator:
    def __init__(self, width, height, difficulty):
        self.width = width
        self.height = height
        self.difficulty = difficulty
        self.maze = [['墙' for _ in range(width)] for _ in range(height)]
        self.start = (1, 1)
        self.exit = (height-2, width-2)
        self._path = []  # 用于保存主路径

    def generate(self):
        """生成保证通路的安全迷宫"""
        max_attempts = 10  # 最大尝试次数防止无限循环
        for _ in range(max_attempts):
            self._generate_base_maze()
            if self._validate_maze():
                self._add_safe_walls()
                if self._validate_maze():
                    return self.maze
        # 如果多次尝试失败，返回无墙版本
        return self._generate_fallback_maze()

    def _generate_base_maze(self):
        """使用改进的Prim算法生成基础迷宫"""
        self.maze = [['墙' for _ in range(self.width)] for _ in range(self.height)]
        frontier = []
        start = self.start
        self.maze[start[0]][start[1]] = '我'
        # 初始化前沿节点
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            nx, ny = start[0]+dx*2, start[1]+dy*2
            if 0 < nx < self.height-1 and 0 < ny < self.width-1:
                frontier.append( (nx, ny, start) )
        
        while frontier:
            x, y, parent = frontier.pop(random.randint(0, len(frontier)-1))
            if self.maze[x][y] == '墙':
                # 打通当前节点与父节点
                mid_x = (x + parent[0]) // 2
                mid_y = (y + parent[1]) // 2
                self.maze[mid_x][mid_y] = '　'
                self.maze[x][y] = '　'
                self._path.append((x,y))
                # 添加新的前沿节点
                for dx, dy in [(-2,0),(2,0),(0,-2),(0,2)]:
                    nx, ny = x+dx, y+dy
                    if 0 < nx < self.height-1 and 0 < ny < self.width-1:
                        if self.maze[nx][ny] == '墙':
                            frontier.append( (nx, ny, (x,y)) )
        
        # 设置出口
        self.maze[self.exit[0]][self.exit[1]] = '门'

    def _add_safe_walls(self):
        """安全添加障碍墙"""
        # 只允许在非主路径区域添加墙
        candidate_positions = []
        for i in range(1, self.height-1):
            for j in range(1, self.width-1):
                if self.maze[i][j] == '　' and (i,j) not in self._path:
                    candidate_positions.append( (i,j) )
        
        # 根据难度计算需要添加的墙数
        wall_count = int(len(candidate_positions) * self.difficulty)
        random.shuffle(candidate_positions)
        
        # 逐个尝试添加墙并验证连通性
        added_walls = 0
        for x, y in candidate_positions:
            if added_walls >= wall_count:
                break
            # 临时设置墙
            original = self.maze[x][y]
            self.maze[x][y] = '墙'
            if self._validate_maze():
                added_walls += 1
            else:
                # 回滚修改
                self.maze[x][y] = original

    def _validate_maze(self):
        """使用BFS验证迷宫连通性"""
        visited = set()
        queue = collections.deque([self.start])
        
        while queue:
            x, y = queue.popleft()
            if (x, y) == self.exit:
                return True
            if (x, y) in visited:
                continue
            visited.add( (x, y) )
            
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                nx, ny = x+dx, y+dy
                if 0 <= nx < self.height and 0 <= ny < self.width:
                    if self.maze[nx][ny] != '墙' and (nx, ny) not in visited:
                        queue.append( (nx, ny) )
        return False

    def _generate_fallback_maze(self):
        """生成保底迷宫（完全连通）"""
        for i in range(1, self.height-1):
            for j in range(1, self.width-1):
                if i % 2 == 1 and j % 2 == 1:
                    self.maze[i][j] = '　'
        self.maze[self.start[0]][self.start[1]] = '我'
        self.maze[self.exit[0]][self.exit[1]] = '门'
        return self.maze

class MazeGame:
    SAVE_FILE = "maze_save.dat"
    MAX_HISTORY = 5
    
    def __init__(self, level=1, move_count=0, total_score=0):
        self.level = level
        self.move_count = move_count
        self.total_score = total_score
        self.start_time = time.time()
        self.history_scores = self._load_history()
        self.sound = SoundManager()
        self.maze = []
        self.player_pos = (0, 0)
        self.exit_pos = (0, 0)
        self._generate_new_maze()
        self.sound = SoundManager()
    def _generate_new_maze(self):
        base_size = 9 + self.level * 2
        difficulty = min(0.3 + self.level*0.02, 0.5)
        generator = MazeGenerator(base_size, base_size, difficulty)
        self.maze = generator.generate()
        for i, row in enumerate(self.maze):
            for j, cell in enumerate(row):
                if cell == '我':
                    self.player_pos = (i, j)
                elif cell == '门':
                    self.exit_pos = (i, j)

    def _clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def display(self):
        self._clear_screen()
        elapsed = int(time.time() - self.start_time)
        print(f"=== 第 {self.level} 关 ===")
        print(f"用时: {elapsed//60:02d}:{elapsed%60:02d} | 步数: {self.move_count}")
        print(f"总得分: {self.total_score} | 历史最高: {max(self.history_scores) if self.history_scores else 0}")
        for row in self.maze:
            print(' '.join(row).replace('墙', '墙').replace('　', '  '))
        print("控制：WASD移动，Q保存退出")

    def move_player(self, direction):
        dx, dy = 0, 0
        direction = direction.lower()
        if direction == 'w': dx = -1
        elif direction == 's': dx = 1
        elif direction == 'a': dy = -1
        elif direction == 'd': dy = 1

        new_x = self.player_pos[0] + dx
        new_y = self.player_pos[1] + dy

        if 0 <= new_x < len(self.maze) and 0 <= new_y < len(self.maze[0]):
            target_cell = self.maze[new_x][new_y]
            if target_cell != '墙':
                self.sound.play('move')  # 只触发音效
                self._update_position(new_x, new_y)
                self.move_count += 1
                return True
            else:
                self.sound.play('wall')
        return False

    def _update_position(self, new_x, new_y):
        self.maze[self.player_pos[0]][self.player_pos[1]] = '　'
        self.player_pos = (new_x, new_y)
        self.maze[new_x][new_y] = '我'

    def check_victory(self):
        if self.player_pos == self.exit_pos:
            self.sound.play('win')  # 胜利音效
            return True
        return False

    def calculate_score(self):
        time_used = time.time() - self.start_time
        time_score = max(0, 1000 - int(time_used * 10))
        move_score = max(0, 500 - self.move_count * 5)
        return time_score + move_score

    def save_game(self):
        data = {
            'level': self.level,
            'move_count': self.move_count,
            'total_score': self.total_score,
            'history': self.history_scores
        }
        try:
            with open(self.SAVE_FILE, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            print(f"保存失败: {str(e)}")

    def _load_history(self):
        try:
            with open(self.SAVE_FILE, 'rb') as f:
                data = pickle.load(f)
                return data.get('history', [])[:self.MAX_HISTORY]
        except:
            return []

    @classmethod
    def load_game(cls):
        try:
            with open(cls.SAVE_FILE, 'rb') as f:
                data = pickle.load(f)
            return cls(data['level'], data['move_count'], data['total_score'])
        except:
            return None

def main():
    game = None
    if os.path.exists(MazeGame.SAVE_FILE):
        print("检测到存档，是否加载？ (y/n)")
        try:
            if input().lower() == 'y':
                game = MazeGame.load_game()
        except:
            pass
    
    if not game:
        game = MazeGame()

    while True:
        game.display()
        
        while True:
            try:
                key = getch().decode().lower()
            except UnicodeDecodeError:
                key = ''
            
            if key == 'q':
                game.save_game()
                print("游戏已保存！")
                return
            if key in ('w', 'a', 's', 'd'):
                if game.move_player(key):
                    game.display()
                    if game.check_victory():
                        level_score = game.calculate_score()
                        game.total_score += level_score
                        game.history_scores.append(game.total_score)
                        game.history_scores = sorted(game.history_scores[-MazeGame.MAX_HISTORY:], reverse=True)
                        
                        print(f"本关得分: {level_score}")
                        print(f"总得分: {game.total_score}")
                        time.sleep(2)
                        
                        game = MazeGame(game.level+1, 0, game.total_score)
                        break
            else:
                game.display()
                print("无效输入！请使用 WASD 移动")

if __name__ == "__main__":
    main()