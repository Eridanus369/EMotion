from PIL import Image, ImageDraw
import math
import os

# 确保icons目录存在
icons_dir = os.path.join(os.path.dirname(__file__), 'icons')
os.makedirs(icons_dir, exist_ok=True)

# 图标尺寸
width = 32
height = 32

# 绘制常值图标
def draw_constant_icon():
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 绘制一个点
    center = (width//2, height//2)
    radius = 4
    draw.ellipse([(center[0]-radius, center[1]-radius), (center[0]+radius, center[1]+radius)], fill='#FF69B4')
    img.save(os.path.join(icons_dir, 'constant.png'))

# 绘制线性+图标
def draw_linear_pos_icon():
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 绘制向上的斜线
    draw.line([(5, height-5), (width-5, 5)], fill='#FF69B4', width=2)
    img.save(os.path.join(icons_dir, 'linear_pos.png'))

# 绘制线性-图标
def draw_linear_neg_icon():
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 绘制向下的斜线
    draw.line([(5, 5), (width-5, height-5)], fill='#FF69B4', width=2)
    img.save(os.path.join(icons_dir, 'linear_neg.png'))

# 绘制线性主图标
def draw_linear_main_icon():
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 绘制两条斜线
    draw.line([(5, height-5), (width-5, 5)], fill='#FF69B4', width=2)
    draw.line([(5, 5), (width-5, height-5)], fill='#FF69B4', width=2)
    img.save(os.path.join(icons_dir, 'linear.png'))

# 绘制正弦图标
def draw_sine_icon():
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 绘制正弦波
    amplitude = height // 3
    center_y = height // 2
    points = []
    for x in range(width):
        rad = x / width * 2 * math.pi
        y = center_y - amplitude * math.sin(rad)
        points.append((x, y))
    draw.line(points, fill='#FF69B4', width=2)
    img.save(os.path.join(icons_dir, 'sine_full.png'))

# 绘制下半正弦图标
def draw_sine_bottom_icon():
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 绘制下半正弦波
    amplitude = height // 3
    center_y = height // 2
    points = []
    for x in range(width):
        rad = x / width * math.pi
        y = center_y + amplitude * math.sin(rad)
        points.append((x, y))
    draw.line(points, fill='#FF69B4', width=2)
    img.save(os.path.join(icons_dir, 'sine_bottom.png'))

# 绘制上半正弦图标
def draw_sine_top_icon():
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 绘制上半正弦波
    amplitude = height // 3
    center_y = height // 2
    points = []
    for x in range(width):
        rad = x / width * math.pi
        y = center_y - amplitude * math.sin(rad)
        points.append((x, y))
    draw.line(points, fill='#FF69B4', width=2)
    img.save(os.path.join(icons_dir, 'sine_top.png'))

# 绘制半周期正弦图标
def draw_sine_half_icon():
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 绘制半周期正弦波
    amplitude = height // 3
    center_y = height // 2
    points = []
    for x in range(width):
        rad = x / width * math.pi
        y = center_y - amplitude * math.sin(rad)
        points.append((x, y))
    draw.line(points, fill='#FF69B4', width=2)
    img.save(os.path.join(icons_dir, 'sine_half.png'))

# 绘制单增半周期正弦图标
def draw_sine_increasing_icon():
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 绘制单增半周期正弦波（从-π/2到π/2）
    amplitude = height // 3
    center_y = height // 2
    points = []
    for x in range(width):
        rad = (x / width) * math.pi - math.pi/2
        y = center_y - amplitude * math.sin(rad)
        points.append((x, y))
    draw.line(points, fill='#FF69B4', width=2)
    img.save(os.path.join(icons_dir, 'sine_increasing.png'))

# 绘制单减半周期正弦图标
def draw_sine_decreasing_icon():
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 绘制单减半周期正弦波（从π/2到3π/2）
    amplitude = height // 3
    center_y = height // 2
    points = []
    for x in range(width):
        rad = (x / width) * math.pi + math.pi/2
        y = center_y - amplitude * math.sin(rad)
        points.append((x, y))
    draw.line(points, fill='#FF69B4', width=2)
    img.save(os.path.join(icons_dir, 'sine_decreasing.png'))

# 绘制正弦主图标
def draw_sine_main_icon():
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 绘制完整正弦波
    amplitude = height // 3
    center_y = height // 2
    points = []
    for x in range(width):
        rad = x / width * 2 * math.pi
        y = center_y - amplitude * math.sin(rad)
        points.append((x, y))
    draw.line(points, fill='#FF69B4', width=2)
    img.save(os.path.join(icons_dir, 'sine.png'))

# 绘制平方根图标
def draw_square_root_icon():
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 绘制平方根曲线
    amplitude = height // 2
    center_y = height // 2
    points = []
    for x in range(width):
        t = x / width
        y = center_y - amplitude * math.sqrt(t)
        points.append((x, y))
    draw.line(points, fill='#FF69B4', width=2)
    img.save(os.path.join(icons_dir, 'square_root.png'))

# 绘制对数图标
def draw_log_icon():
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 绘制对数曲线
    amplitude = height // 4
    center_y = height // 2
    points = []
    for x in range(1, width):
        t = x / width
        y = center_y - amplitude * math.log(t + 0.1)
        points.append((x, y))
    draw.line(points, fill='#FF69B4', width=2)
    img.save(os.path.join(icons_dir, 'natural_log.png'))

# 绘制非线性主图标
def draw_nonlinear_main_icon():
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 绘制非线性曲线（平方根）
    amplitude = height // 3
    center_y = height // 2
    points = []
    for x in range(width):
        t = x / width
        y = center_y - amplitude * math.sqrt(t)
        points.append((x, y))
    draw.line(points, fill='#FF69B4', width=2)
    img.save(os.path.join(icons_dir, 'nonlinear.png'))

# 绘制贝塞尔图标
def draw_bezier_icon():
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 绘制贝塞尔曲线
    start = (5, height//2)
    control1 = (width//3, 5)
    control2 = (2*width//3, height-5)
    end = (width-5, height//2)
    
    # 贝塞尔曲线
    points = []
    steps = 20
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        x = int(u*u*u*start[0] + 3*u*u*t*control1[0] + 3*u*t*t*control2[0] + t*t*t*end[0])
        y = int(u*u*u*start[1] + 3*u*u*t*control1[1] + 3*u*t*t*control2[1] + t*t*t*end[1])
        points.append((x, y))
    draw.line(points, fill='#FF69B4', width=2)
    img.save(os.path.join(icons_dir, 'custom_bezier.png'))

# 绘制贝塞尔主图标
def draw_bezier_main_icon():
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 绘制贝塞尔曲线
    start = (5, height//2)
    control1 = (width//3, 5)
    control2 = (2*width//3, height-5)
    end = (width-5, height//2)
    
    # 贝塞尔曲线
    points = []
    steps = 20
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        x = int(u*u*u*start[0] + 3*u*u*t*control1[0] + 3*u*t*t*control2[0] + t*t*t*end[0])
        y = int(u*u*u*start[1] + 3*u*u*t*control1[1] + 3*u*t*t*control2[1] + t*t*t*end[1])
        points.append((x, y))
    draw.line(points, fill='#FF69B4', width=2)
    img.save(os.path.join(icons_dir, 'bezier.png'))

# 绘制步进图标
def draw_stepped_icon():
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 绘制步进曲线
    steps = 4
    step_width = width // steps
    center_y = height // 2
    amplitude = height // 4
    
    points = []
    for i in range(steps + 1):
        x = i * step_width
        y = center_y + (amplitude if i % 2 == 0 else -amplitude)
        points.append((x, y))
    draw.line(points, fill='#FF69B4', width=2)
    img.save(os.path.join(icons_dir, 'stepped_linear.png'))

# 绘制正弦步进图标
def draw_sine_stepped_icon():
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 绘制正弦步进曲线
    steps = 4
    step_width = width // steps
    center_y = height // 2
    amplitude = height // 4
    
    points = []
    for i in range(steps + 1):
        x = i * step_width
        t = i / steps
        y = center_y - amplitude * math.sin(t * 2 * math.pi)
        points.append((x, y))
    draw.line(points, fill='#FF69B4', width=2)
    img.save(os.path.join(icons_dir, 'sine_stepped.png'))

# 绘制噪声图标
def draw_noise_icon():
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 绘制噪声曲线
    import random
    random.seed(42)
    center_y = height // 2
    amplitude = height // 3
    
    points = []
    for x in range(width):
        y = center_y + (random.random() - 0.5) * amplitude
        points.append((x, y))
    draw.line(points, fill='#FF69B4', width=2)
    img.save(os.path.join(icons_dir, 'noise.png'))

# 绘制叠加主图标
def draw_overlay_main_icon():
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 绘制叠加图标（步进+正弦）
    steps = 4
    step_width = width // steps
    center_y = height // 2
    amplitude = height // 4
    
    points = []
    for i in range(steps + 1):
        x = i * step_width
        t = i / steps
        y = center_y - amplitude * math.sin(t * 2 * math.pi)
        points.append((x, y))
    draw.line(points, fill='#FF69B4', width=2)
    img.save(os.path.join(icons_dir, 'overlay.png'))

# 生成所有图标
def generate_all_icons():
    print("生成图标中...")
    
    # 线性类别
    draw_linear_main_icon()
    draw_constant_icon()
    draw_linear_pos_icon()
    draw_linear_neg_icon()
    
    # 正弦类别
    draw_sine_main_icon()
    draw_sine_icon()
    draw_sine_bottom_icon()
    draw_sine_top_icon()
    draw_sine_half_icon()
    draw_sine_increasing_icon()
    draw_sine_decreasing_icon()
    
    # 非线性类别
    draw_nonlinear_main_icon()
    draw_square_root_icon()
    draw_log_icon()
    
    # 贝塞尔类别
    draw_bezier_main_icon()
    draw_bezier_icon()
    
    # 叠加类别
    draw_overlay_main_icon()
    draw_stepped_icon()
    draw_sine_stepped_icon()
    draw_noise_icon()
    
    print(f"所有图标已生成到 {icons_dir}")

if __name__ == "__main__":
    generate_all_icons()