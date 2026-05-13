#!/usr/bin/env python3
"""
俄罗斯方块游戏 (Tetris)
使用 Pygame 库实现经典俄罗斯方块游戏

控制说明:
- ← → : 左右移动
- ↑ : 旋转
- ↓ : 加速下落
- 空格 : 硬降（直接落到底部）
- P : 暂停/继续
- R : 重新开始（游戏结束后）
- ESC : 退出
"""

import pygame
import random
import sys

# 初始化 Pygame
pygame.init()

# 游戏常量
BLOCK_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
SCREEN_WIDTH = BLOCK_SIZE * (GRID_WIDTH + 8)
SCREEN_HEIGHT = BLOCK_SIZE * GRID_HEIGHT

# 颜色定义
COLORS = {
    'black': (0, 0, 0),
    'white': (255, 255, 255),
    'gray': (128, 128, 128),
    'cyan': (0, 255, 255),      # I型
    'yellow': (255, 255, 0),    # O型
    'purple': (128, 0, 128),    # T型
    'green': (0, 255, 0),       # S型
    'red': (255, 0, 0),         # Z型
    'blue': (0, 0, 255),        # J型
    'orange': (255, 165, 0),    # L型
    'dark_gray': (40, 40, 40),
    'light_gray': (100, 100, 100),
}

# 方块形状定义（每个元组代表一种旋转状态）
SHAPES = {
    'I': [
        [(0,1), (1,1), (2,1), (3,1)],
        [(2,0), (2,1), (2,2), (2,3)],
        [(0,2), (1,2), (2,2), (3,2)],
        [(1,0), (1,1), (1,2), (1,3)],
    ],
    'O': [
        [(1,0), (2,0), (1,1), (2,1)],
        [(1,0), (2,0), (1,1), (2,1)],
        [(1,0), (2,0), (1,1), (2,1)],
        [(1,0), (2,0), (1,1), (2,1)],
    ],
    'T': [
        [(1,0), (0,1), (1,1), (2,1)],
        [(1,0), (1,1), (2,1), (1,2)],
        [(0,1), (1,1), (2,1), (1,2)],
        [(1,0), (0,1), (1,1), (1,2)],
    ],
    'S': [
        [(1,0), (2,0), (0,1), (1,1)],
        [(1,0), (1,1), (2,1), (2,2)],
        [(1,1), (2,1), (0,2), (1,2)],
        [(0,0), (0,1), (1,1), (1,2)],
    ],
    'Z': [
        [(0,0), (1,0), (1,1), (2,1)],
        [(2,0), (1,1), (2,1), (1,2)],
        [(0,1), (1,1), (1,2), (2,2)],
        [(1,0), (0,1), (1,1), (0,2)],
    ],
    'J': [
        [(0,0), (0,1), (1,1), (2,1)],
        [(1,0), (2,0), (1,1), (1,2)],
        [(0,1), (1,1), (2,1), (2,2)],
        [(1,0), (1,1), (0,2), (1,2)],
    ],
    'L': [
        [(2,0), (0,1), (1,1), (2,1)],
        [(1,0), (1,1), (1,2), (2,2)],
        [(0,1), (1,1), (2,1), (0,2)],
        [(0,0), (1,0), (1,1), (1,2)],
    ],
}

# 方块颜色
SHAPE_COLORS = {
    'I': COLORS['cyan'],
    'O': COLORS['yellow'],
    'T': COLORS['purple'],
    'S': COLORS['green'],
    'Z': COLORS['red'],
    'J': COLORS['blue'],
    'L': COLORS['orange'],
}


class Tetromino:
    """方块类"""
    def __init__(self):
        self.shape_type = random.choice(list(SHAPES.keys()))
        self.color = SHAPE_COLORS[self.shape_type]
        self.rotation = 0
        self.x = GRID_WIDTH // 2 - 2
        self.y = 0
    
    def get_blocks(self):
        """获取方块当前状态的格子位置"""
        return SHAPES[self.shape_type][self.rotation]
    
    def get_absolute_positions(self):
        """获取方块在游戏板上的绝对位置"""
        positions = []
        for (bx, by) in self.get_blocks():
            positions.append((self.x + bx, self.y + by))
        return positions
    
    def rotate(self):
        """旋转方块"""
        self.rotation = (self.rotation + 1) % 4
    
    def unrotate(self):
        """反旋转（用于碰撞检测）"""
        self.rotation = (self.rotation - 1) % 4


class Tetris:
    """游戏主类"""
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('俄罗斯方块 (Tetris)')
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        self.reset_game()
    
    def reset_game(self):
        """重置游戏"""
        self.board = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = Tetromino()
        self.next_piece = Tetromino()
        self.game_over = False
        self.paused = False
        self.score = 0
        self.lines_cleared = 0
        self.level = 1
        self.fall_time = 0
        self.fall_speed = 500  # 毫秒
        self.lock_delay = 0
        self.lock_delay_max = 500  # 触底后锁定前的延迟
    
    def is_valid_position(self, piece, dx=0, dy=0, rotation=None):
        """检查方块位置是否有效"""
        if rotation is None:
            rotation = piece.rotation
        
        old_rotation = piece.rotation
        piece.rotation = rotation
        
        valid = True
        for (bx, by) in piece.get_blocks():
            x = piece.x + bx + dx
            y = piece.y + by + dy
            
            if x < 0 or x >= GRID_WIDTH or y >= GRID_HEIGHT:
                valid = False
                break
            if y >= 0 and self.board[y][x] is not None:
                valid = False
                break
        
        piece.rotation = old_rotation
        return valid
    
    def lock_piece(self):
        """锁定当前方块到游戏板"""
        for (x, y) in self.current_piece.get_absolute_positions():
            if y >= 0:
                self.board[y][x] = self.current_piece.color
        
        self.clear_lines()
        self.current_piece = self.next_piece
        self.next_piece = Tetromino()
        self.lock_delay = 0
        
        # 检查游戏结束
        if not self.is_valid_position(self.current_piece):
            self.game_over = True
    
    def clear_lines(self):
        """消除满行"""
        lines_to_clear = []
        
        for y in range(GRID_HEIGHT):
            if all(self.board[y][x] is not None for x in range(GRID_WIDTH)):
                lines_to_clear.append(y)
        
        if lines_to_clear:
            # 消除行
            for y in sorted(lines_to_clear, reverse=True):
                del self.board[y]
                self.board.insert(0, [None for _ in range(GRID_WIDTH)])
            
            # 计分
            num_lines = len(lines_to_clear)
            points = {
                1: 100,
                2: 300,
                3: 500,
                4: 800,
            }
            self.score += points.get(num_lines, 100 * num_lines)
            self.lines_cleared += num_lines
            
            # 升级
            new_level = self.lines_cleared // 10 + 1
            if new_level > self.level:
                self.level = new_level
                self.fall_speed = max(100, 500 - (self.level - 1) * 50)
    
    def move_piece(self, dx, dy):
        """移动方块"""
        if self.is_valid_position(self.current_piece, dx, dy):
            self.current_piece.x += dx
            self.current_piece.y += dy
            if dy == 0:
                self.lock_delay = 0
            return True
        return False
    
    def rotate_piece(self):
        """旋转方块"""
        new_rotation = (self.current_piece.rotation + 1) % 4
        
        # 尝试基本旋转
        if self.is_valid_position(self.current_piece, rotation=new_rotation):
            self.current_piece.rotation = new_rotation
            self.lock_delay = 0
            return True
        
        # 墙踢 (Wall Kick) - 尝试左右偏移
        kicks = [-1, 1, -2, 2]
        for kick in kicks:
            if self.is_valid_position(self.current_piece, kick, 0, new_rotation):
                self.current_piece.x += kick
                self.current_piece.rotation = new_rotation
                self.lock_delay = 0
                return True
        
        return False
    
    def hard_drop(self):
        """硬降（直接落到底部）"""
        drop_distance = 0
        while self.move_piece(0, 1):
            drop_distance += 1
        self.score += drop_distance * 2
        self.lock_piece()
    
    def update(self, dt):
        """更新游戏状态"""
        if self.game_over or self.paused:
            return
        
        self.fall_time += dt
        
        # 检查是否触底或悬浮
        if not self.is_valid_position(self.current_piece, 0, 1):
            # 触底
            self.lock_delay += dt
            if self.lock_delay >= self.lock_delay_max:
                self.lock_piece()
        else:
            self.lock_delay = 0
            if self.fall_time >= self.fall_speed:
                self.move_piece(0, 1)
                self.fall_time = 0
    
    def draw_block(self, x, y, color, surface=None):
        """绘制单个方块"""
        if surface is None:
            surface = self.screen
        
        rect = pygame.Rect(x, y, BLOCK_SIZE - 1, BLOCK_SIZE - 1)
        pygame.draw.rect(surface, color, rect)
        
        # 添加3D效果
        light = tuple(min(255, c + 50) for c in color)
        dark = tuple(max(0, c - 50) for c in color)
        
        pygame.draw.line(surface, light, (x, y), (x + BLOCK_SIZE - 1, y), 2)
        pygame.draw.line(surface, light, (x, y), (x, y + BLOCK_SIZE - 1), 2)
        pygame.draw.line(surface, dark, (x + BLOCK_SIZE - 1, y), (x + BLOCK_SIZE - 1, y + BLOCK_SIZE - 1), 2)
        pygame.draw.line(surface, dark, (x, y + BLOCK_SIZE - 1), (x + BLOCK_SIZE - 1, y + BLOCK_SIZE - 1), 2)
    
    def draw(self):
        """绘制游戏画面"""
        self.screen.fill(COLORS['dark_gray'])
        
        # 绘制游戏区域边框
        pygame.draw.rect(self.screen, COLORS['light_gray'], 
                        (0, 0, BLOCK_SIZE * GRID_WIDTH, BLOCK_SIZE * GRID_HEIGHT), 2)
        
        # 绘制已固定的方块
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if self.board[y][x]:
                    self.draw_block(x * BLOCK_SIZE, y * BLOCK_SIZE, self.board[y][x])
        
        # 绘制当前方块的投影
        if not self.game_over and not self.paused:
            drop_y = 0
            while self.is_valid_position(self.current_piece, 0, drop_y + 1):
                drop_y += 1
            
            for (bx, by) in self.current_piece.get_blocks():
                ghost_x = self.current_piece.x + bx
                ghost_y = self.current_piece.y + by + drop_y
                if ghost_y >= 0:
                    rect = pygame.Rect(ghost_x * BLOCK_SIZE + 2, 
                                      ghost_y * BLOCK_SIZE + 2, 
                                      BLOCK_SIZE - 5, BLOCK_SIZE - 5)
                    pygame.draw.rect(self.screen, COLORS['gray'], rect, 2)
        
        # 绘制当前方块
        if not self.game_over:
            for (bx, by) in self.current_piece.get_absolute_positions():
                if by >= 0:
                    self.draw_block(bx * BLOCK_SIZE, by * BLOCK_SIZE, 
                                  self.current_piece.color)
        
        # 绘制右侧信息面板
        panel_x = BLOCK_SIZE * GRID_WIDTH + 20
        
        # 下一个方块
        next_text = self.font.render('下一个:', True, COLORS['white'])
        self.screen.blit(next_text, (panel_x, 20))
        
        preview_size = 4 * BLOCK_SIZE
        preview_surface = pygame.Surface((preview_size, preview_size))
        preview_surface.fill(COLORS['dark_gray'])
        
        for (bx, by) in self.next_piece.get_blocks():
            self.draw_block(bx * (BLOCK_SIZE // 2), by * (BLOCK_SIZE // 2), 
                          self.next_piece.color, preview_surface)
        
        self.screen.blit(preview_surface, (panel_x, 50))
        
        # 分数
        score_text = self.font.render('分数:', True, COLORS['white'])
        self.screen.blit(score_text, (panel_x, 150))
        score_value = self.font.render(str(self.score), True, COLORS['yellow'])
        self.screen.blit(score_value, (panel_x, 180))
        
        # 消除行数
        lines_text = self.font.render('行数:', True, COLORS['white'])
        self.screen.blit(lines_text, (panel_x, 230))
        lines_value = self.font.render(str(self.lines_cleared), True, COLORS['yellow'])
        self.screen.blit(lines_value, (panel_x, 260))
        
        # 等级
        level_text = self.font.render('等级:', True, COLORS['white'])
        self.screen.blit(level_text, (panel_x, 310))
        level_value = self.font.render(str(self.level), True, COLORS['yellow'])
        self.screen.blit(level_value, (panel_x, 340))
        
        # 控制说明
        controls = [
            '控制:',
            '← → 移动',
            '↑ 旋转',
            '↓ 加速',
            '空格 落下',
            'P 暂停',
            'ESC 退出',
        ]
        
        y_pos = 400
        for line in controls:
            text = self.small_font.render(line, True, COLORS['gray'])
            self.screen.blit(text, (panel_x, y_pos))
            y_pos += 22
        
        # 游戏结束/暂停提示
        if self.game_over:
            self.draw_centered_text('游戏结束!', COLORS['red'], 72)
            self.draw_centered_text(f'最终分数: {self.score}', COLORS['white'], 36, 100)
            restart_text = self.small_font.render('按 R 重新开始', True, COLORS['gray'])
            self.screen.blit(restart_text, restart_text.get_rect(center=(SCREEN_WIDTH // 2, 150)))
        
        elif self.paused:
            self.draw_centered_text('暂停', COLORS['yellow'], 48)
        
        pygame.display.flip()
    
    def draw_centered_text(self, text, color, size, y_offset=0):
        """绘制居中文本"""
        font = pygame.font.Font(None, size)
        text_surface = font.render(text, True, color)
        rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + y_offset))
        
        # 背景遮罩
        bg_rect = rect.inflate(20, 10)
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
        bg_surface.fill(COLORS['dark_gray'])
        bg_surface.set_alpha(200)
        self.screen.blit(bg_surface, bg_rect)
        
        self.screen.blit(text_surface, rect)
    
    def handle_events(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                
                if self.game_over:
                    if event.key == pygame.K_r:
                        self.reset_game()
                    continue
                
                if event.key == pygame.K_p:
                    self.paused = not self.paused
                    continue
                
                if self.paused:
                    continue
                
                if event.key == pygame.K_LEFT:
                    self.move_piece(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    self.move_piece(1, 0)
                elif event.key == pygame.K_DOWN:
                    if self.move_piece(0, 1):
                        self.score += 1
                elif event.key == pygame.K_UP:
                    self.rotate_piece()
                elif event.key == pygame.K_SPACE:
                    self.hard_drop()
        
        return True
    
    def run(self):
        """主游戏循环"""
        running = True
        
        while running:
            dt = self.clock.tick(60)  # 60 FPS
            
            running = self.handle_events()
            self.update(dt)
            self.draw()
        
        pygame.quit()


def main():
    """主函数"""
    game = Tetris()
    game.run()


if __name__ == '__main__':
    main()
