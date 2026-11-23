from lib import *
import random
from collections import deque

random.seed(4)
N, CELL, GX, GY = 18, 32, 72, 330
MOVES_PER_SEC = 20
snake = deque([(5, 9), (4, 9), (3, 9), (2, 9)])
food = (12, 9)
score = 0
eat_times = []


def new_food():
    free = [(x, y) for x in range(N) for y in range(N) if (x, y) not in snake]
    return random.choice(free)


def bfs(start, goal, body):
    blocked = set(list(body)[:-1])
    q = deque([start]); prev = {start: None}
    while q:
        c = q.popleft()
        if c == goal: break
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (c[0] + dx, c[1] + dy)
            if 0 <= n[0] < N and 0 <= n[1] < N and n not in blocked and n not in prev:
                prev[n] = c; q.append(n)
    if goal not in prev: return None
    path = []; c = goal
    while prev[c] is not None: path.append(c); c = prev[c]
    return path[::-1]


def step(t):
    global food, score
    path = bfs(snake[0], food, snake)
    if path: nxt = path[0]
    else:  # survive: any free neighbour
        hx, hy = snake[0]
        opts = [(hx + dx, hy + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        opts = [o for o in opts if 0 <= o[0] < N and 0 <= o[1] < N and o not in list(snake)[:-1]]
        nxt = opts[0] if opts else snake[0]
    snake.appendleft(nxt)
    if nxt == food:
        score += 1; eat_times.append(t); food = new_food()
    else:
        snake.pop()


bg = vgradient(RW, RH, (8, 20, 18), (2, 6, 6))
bd = ImageDraw.Draw(bg)
bd.rounded_rectangle([(GX - 10) * SS, (GY - 10) * SS, (GX + N * CELL + 10) * SS, (GY + N * CELL + 10) * SS],
                     radius=16 * SS, fill=(14, 34, 30), outline=(40, 120, 90), width=3 * SS)
for x in range(N):
    for y in range(N):
        if (x + y) % 2:
            bd.rectangle([(GX + x * CELL) * SS, (GY + y * CELL) * SS, (GX + x * CELL + CELL) * SS,
                          (GY + y * CELL + CELL) * SS], fill=(17, 40, 35))

with Video("8_ai_snake.mp4") as v:
    v.audio += beat(5, bpm=150, kick_steps=(0, 4, 8, 12), snare_steps=(4, 12), gain=0.3)
    moves_done = 0
    for f in range(v.nframes):
        t = f / FPS
        while moves_done < int(max(t - 0.4, 0) * MOVES_PER_SEC):
            moves_done += 1; step(0.4 + moves_done / MOVES_PER_SEC)
        img = bg.copy(); d = ImageDraw.Draw(img, "RGBA")
        L = len(snake)
        for i, (x, y) in enumerate(reversed(snake)):
            k = (i + 1) / L
            c = (int(40 + 60 * k), int(150 + 100 * k), int(90 + 40 * k))
            pad_ = 3 if i < L - 1 else 1
            d.rounded_rectangle([(GX + x * CELL + pad_) * SS, (GY + y * CELL + pad_) * SS,
                                 (GX + x * CELL + CELL - pad_) * SS, (GY + y * CELL + CELL - pad_) * SS],
                                radius=8 * SS, fill=c)
        hx, hy = snake[0]
        for ex in (10, 22):
            d.ellipse([(GX + hx * CELL + ex - 3) * SS, (GY + hy * CELL + 10) * SS, (GX + hx * CELL + ex + 3) * SS,
                       (GY + hy * CELL + 16) * SS], fill=(10, 20, 15))
        fx, fy = food; pul = 3 * math.sin(t * 10)
        d.ellipse([(GX + fx * CELL + 4 - pul) * SS, (GY + fy * CELL + 4 - pul) * SS,
                   (GX + fx * CELL + CELL - 4 + pul) * SS, (GY + fy * CELL + CELL - 4 + pul) * SS], fill=(255, 70, 90))
        for et in eat_times[-3:]:
            u = (t - et) / 0.4
            if 0 <= u < 1:
                text(d, (W / 2, 1000 - 40 * u), "+1", 40, (255, 230, 80, int(255 * (1 - u))))
        text(d, (W / 2, 110), "AI speelt Snake", 58, (120, 255, 170), stroke=5, stroke_fill=(0, 0, 0))
        text(d, (W / 2, 180), "zoekt zelf de kortste weg", 30, (180, 220, 200))
        text(d, (W / 2, 280), f"Score: {score}", 40, (255, 255, 255))
        text(d, (W / 2, 1100), "Hoe ver komt hij?", 40, (255, 255, 255), stroke=4, stroke_fill=(0, 0, 0))
        v.add(img)
    for i, et in enumerate(eat_times):
        v.sfx(et, pluck(note(72 + [0, 2, 4, 7, 9, 12][i % 6])), 0.9)
        v.sfx(et, click(2400, 0.04), 0.4)
print("score", score)
