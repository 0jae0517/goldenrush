import pygame
import random
import sys
import os
import math
import cv2
import numpy as np


# 파이썬 실행 위치를 현재 파일이 있는 폴더로 고정
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# --- [설정] 게임 및 화면 크기 ---
TILE_SIZE = 108
FPS = 60

# ==========================================
# 실제 맵 디자인과 100% 일치하도록 데이터 설정
# ==========================================
MAP_DATA = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 2, 1, 0, 3, 1, 0, 0, 1, 0, 3, 1, 0, 1],
    [1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 3, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 1],
    [1, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 3, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 1],
    [1, 0, 1, 2, 0, 1, 0, 3, 1, 0, 0, 1, 2, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
]

# --- 환자 발생(ON) 집 이미지 매핑 ---
ON_HOUSE_IMAGES = {
    (12, 2): "on_building.png",
    (10, 1): "on_building.png",
    (3, 5):  "on_building.png",
    (4, 1):  "on_building.png",
    (11, 5): "on_building.png",
    (7, 8):  "on_building.png"  
}

# --- 튜토리얼 맵 데이터 ---
# --- 수정 후 ---
# 튜토리얼 맵 데이터 (14x10 크기로 확장, 5,5 위치에 환자 배치)
TUTORIAL_MAP = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2], # 2: 병원(13,4)
    [0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0], # 3: 환자(5,5) - 한 칸 내림
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
]

GAME_WIDTH = len(MAP_DATA[0]) * TILE_SIZE
GAME_HEIGHT = len(MAP_DATA) * TILE_SIZE
HUD_WIDTH = 408
HUD_HEIGHT = 1080

SCREEN_WIDTH = GAME_WIDTH + HUD_WIDTH
SCREEN_HEIGHT = HUD_HEIGHT

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
GREEN = (50, 200, 50)
BLUE = (50, 50, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)

# 등장 동물(순환)
ANIMAL_NAMES = ["dog", "bear", "fox", "neulbo", "owl", "panda", "rabbit", "squirrel"]

# =========================
# [Stage2 병원 활성/비활성]
# =========================
HOSPITAL_COORDS = [(1, 1), (9, 4), (3, 8), (12, 8)]

# 활성/비활성 병원 이미지 파일명
HOSPITAL_ACTIVE_IMG = "hospital_on.png"
HOSPITAL_INACTIVE_IMG = "hospital_off.png"

def pick_active_hospitals(stage: int) -> set[tuple[int, int]]:
    if stage == 1:
        return set(HOSPITAL_COORDS)  # Stage1: 전부 활성
    if stage == 2:
        return set(random.sample(HOSPITAL_COORDS, 2))  # Stage2: 2개만 랜덤 활성
    return set(HOSPITAL_COORDS)


# ----------------------------
# [유틸] 커스텀 폰트 로드 함수
# ----------------------------
def get_custom_font(size, bold=False):
    font_path = os.path.join("asset", "font", "Galmuri9.ttf")
    try:
        font = pygame.font.Font(font_path, size)
        if bold:
            font.set_bold(True)
        return font
    except Exception:
        return pygame.font.SysFont("malgungothic", size, bold=bold)


# ----------------------------
# [유틸] 이미지 로드 함수
# ----------------------------
def load_image(path: str, size: tuple[int, int], text_fallback: str = "") -> pygame.Surface:
    w, h = size
    try:
        if not os.path.exists(path):
            raise FileNotFoundError
        img = pygame.image.load(path).convert_alpha()
        return pygame.transform.smoothscale(img, (w, h))
    except Exception:
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        if "road" in str(path) or "Untitled" in str(path) or "sliced_map" in str(path):
            color = (100, 100, 100, 150)
        elif "hospital" in str(path):
            color = BLUE
        elif "ambulance" in str(path):
            color = RED
        else:
            color = (50, 50, 60, 230)

        surf.fill(color)
        pygame.draw.rect(surf, (200, 200, 200), surf.get_rect(), 2)

        if text_fallback:
            font = get_custom_font(max(14, int(h * 0.35)), bold=True)
            txt = font.render(text_fallback, True, WHITE)
            surf.blit(txt, txt.get_rect(center=(w // 2, h // 2)))
        return surf


def brighten(surf, add=70):
    out = surf.copy()
    out.fill((add, add, add, 0), special_flags=pygame.BLEND_RGB_ADD)
    return out


def draw_text(surf, text, font, color, x, y, align="topleft"):
    img = font.render(text, True, color)
    rect = img.get_rect()
    setattr(rect, align, (x, y))
    surf.blit(img, rect)


def format_time(seconds):
    s = max(0, int(seconds))
    return f"{s // 60:02d}:{s % 60:02d}"


# ----------------------------
# [BGM 유틸]
# ----------------------------
def _find_sound_file(base_dir: str, name: str) -> str | None:
    """확장자 미지정 대비(.mp3/.wav/.ogg) 자동 탐색"""
    exts = [".mp3", ".wav", ".ogg"]
    for ext in exts:
        p = os.path.join(base_dir, name + ext)
        if os.path.exists(p):
            return p
    return None


def init_audio():
    # 너무 늦게 init하면 일부 PC에서 소리 딜레이/깨짐이 있어 미리 pre_init 권장
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.mixer.init()


def play_bgm(track_key: str, fade_ms: int = 600, volume: float = 0.5):
    """
    track_key: "start_screen" / "tutorial" / "game_ing"
    """
    base = os.path.join("asset", "bgm")  # 폴더 원하면 바꿔도 됨 (예: asset/bgm)
    path = _find_sound_file(base, track_key)
    if path is None:
        print(f"[BGM] 파일을 찾지 못함: {os.path.join(base, track_key)}(.mp3/.wav/.ogg)")
        return

    # 이미 같은 곡 재생 중이면 재로딩/재시작 안 함
    current = getattr(play_bgm, "_current", None)
    if current == path and pygame.mixer.music.get_busy():
        return

    try:
        pygame.mixer.music.fadeout(fade_ms)
    except Exception:
        pass

    pygame.mixer.music.load(path)
    pygame.mixer.music.set_volume(volume)
    pygame.mixer.music.play(-1, fade_ms=fade_ms)  # 무한 반복
    play_bgm._current = path
    
# BGM 정지 함수 추가 (유틸 위치)
def stop_bgm():
    try:
        pygame.mixer.music.stop()   # ✅ 즉시 정지
    except Exception:
        pass
    play_bgm._current = None        # ✅ 다음 재생은 무조건 처음부터

# ----------------------------
# [효과음 유틸]
# ----------------------------
def play_game_over_sound(volume: float = 0.7):
    base = os.path.join("asset", "sfx")
    path = _find_sound_file(base, "game_over")  # game_over.mp3 / .wav / .ogg

    if path is None:
        print("[SFX] game_over 파일을 찾지 못함")
        return

    try:
        sound = pygame.mixer.Sound(path)
        sound.set_volume(volume)
        sound.play()   # ✅ 한 번만 재생
    except Exception as e:
        print("game_over 재생 오류:", e)

def play_fake_tel_sound(volume: float = 0.7):
    base = os.path.join("asset", "sfx")
    path = _find_sound_file(base, "fake_tel")  # fake_tel.mp3 / .wav / .ogg

    if path is None:
        print("[SFX] fake_tel 파일을 찾지 못함")
        return

    try:
        sound = pygame.mixer.Sound(path)
        sound.set_volume(volume)
        sound.play()  # ✅ 한 번만 재생
    except Exception as e:
        print("fake_tel 재생 오류:", e)
        
        
# ----------------------------
# [헬기 SFX: 루프/원샷]
# ----------------------------
_HELI_LOOP_CH = None  # 헬기 루프 재생용 채널 (전역)

def _get_heli_loop_channel() -> pygame.mixer.Channel:
    global _HELI_LOOP_CH
    if _HELI_LOOP_CH is None:
        _HELI_LOOP_CH = pygame.mixer.Channel(6)  # 채널 번호는 다른 SFX랑 안 겹치게 아무거나(0~7 등)
    return _HELI_LOOP_CH

def play_item_heli_sound(volume: float = 0.8):
    base = os.path.join("asset", "sfx")
    path = _find_sound_file(base, "item_heli")  # item_heli.mp3 / .wav / .ogg
    if path is None:
        print("[SFX] item_heli 파일을 찾지 못함")
        return
    try:
        s = pygame.mixer.Sound(path)
        s.set_volume(volume)
        s.play()  # ✅ 한 번만
    except Exception as e:
        print("item_heli 재생 오류:", e)

def start_heli_loop(volume: float = 0.45):
    """헬기 탑승 중 지속 소리(루프). 이미 재생 중이면 다시 시작 안 함."""
    base = os.path.join("asset", "sfx")
    path = _find_sound_file(base, "heli")  # heli.mp3 / .wav / .ogg
    if path is None:
        print("[SFX] heli 파일을 찾지 못함")
        return

    try:
        ch = _get_heli_loop_channel()
        if ch.get_busy():
            return  # ✅ 이미 루프 중이면 중복 재생 방지

        s = pygame.mixer.Sound(path)
        s.set_volume(volume)
        ch.play(s, loops=-1)  # ✅ 무한 루프
    except Exception as e:
        print("heli 루프 재생 오류:", e)

def stop_heli_loop():
    """헬기 루프 소리 정지"""
    try:
        ch = _get_heli_loop_channel()
        ch.stop()
    except Exception:
        pass
 
 ######## 골든타임 효과음
def play_time_limit_sound(volume: float = 0.85):
    base = os.path.join("asset", "sfx")
    path = _find_sound_file(base, "time_limit")  # time_limit.mp3 / .wav / .ogg
    if path is None:
        print("[SFX] time_limit 파일을 찾지 못함")
        return
    try:
        s = pygame.mixer.Sound(path)
        s.set_volume(volume)
        s.play()  # ✅ 한 번만
    except Exception as e:
        print("time_limit 재생 오류:", e)
        
# ----------------------------
# [Stage 결과창]
# ----------------------------
def show_stage_result_screen(screen, clock, bg_image_path,
                             stage,
                             saved_count, failed_count,
                             saved_animal_names, failed_animal_names):
    bg = load_image(bg_image_path, (SCREEN_WIDTH, SCREEN_HEIGHT), "")

    title_font = get_custom_font(56, bold=True)
    text_font = get_custom_font(40, bold=True)
    sub_font = get_custom_font(26)

    panel_w, panel_h = 980, 420
    panel = pygame.Rect(
        (SCREEN_WIDTH - panel_w) // 2,
        (SCREEN_HEIGHT - panel_h) // 2,
        panel_w,
        panel_h
    )

    badge_h = 90
    badge = pygame.Rect(panel.x + 40, panel.y - 55, 360, badge_h)

    icon_size = 80
    gap = 10
    max_x = panel.right - 50

    # 성공 동물 smiling
    smiling_surfs = []
    for name in saved_animal_names:
        path = os.path.join("asset", "ui", f"{name}_smiling.png")
        smiling_surfs.append(load_image(path, (icon_size, icon_size), name[:2].upper()))

    # 실패 동물 crying
    crying_surfs = []
    for name in failed_animal_names:
        path = os.path.join("asset", "ui", f"{name}_crying.png")
        crying_surfs.append(load_image(path, (icon_size, icon_size), name[:2].upper()))

    while True:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "QUIT"
                if event.key == pygame.K_RETURN:
                    return "CONTINUE"

        screen.blit(bg, (0, 0))

        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 35))
        screen.blit(dim, (0, 0))

        pygame.draw.rect(screen, (190, 35, 35), badge, border_radius=22)
        pygame.draw.rect(screen, (90, 10, 10), badge, 6, border_radius=22)
        draw_text(screen, "RESULT", title_font, (255, 220, 120), badge.centerx, badge.centery, "center")

        x_text = panel.x + 90
        y_text = panel.y + 110
        draw_text(screen, f"Stage {stage}에 살린 환자:  {saved_count}", text_font, WHITE, x_text, y_text, "topleft")
        draw_text(screen, f"살리지 못한 환자:  {failed_count}", text_font, WHITE, x_text, y_text + 120, "topleft")

        save_icons_start_x = x_text
        save_icons_start_y = y_text + 35
        ix, iy = save_icons_start_x, save_icons_start_y
        for surf in smiling_surfs:
            if ix + icon_size > max_x:
                ix = save_icons_start_x
                iy += icon_size + gap
            screen.blit(surf, (ix, iy))
            ix += icon_size + gap

        fail_icons_start_x = x_text
        fail_icons_start_y = y_text + 165
        ix, iy = fail_icons_start_x, fail_icons_start_y
        for surf in crying_surfs:
            if ix + icon_size > max_x:
                ix = fail_icons_start_x
                iy += icon_size + gap
            screen.blit(surf, (ix, iy))
            ix += icon_size + gap

        draw_text(screen, "[ENTER] 계속  /  [ESC] 종료", sub_font, (60, 60, 60),
                  panel.centerx, panel.bottom - 30, "center")

        pygame.display.flip()

###### thank you 효과음 유틸
def play_thank_you_sound(volume: float = 0.85):
    base = os.path.join("asset", "sfx")
    path = _find_sound_file(base, "thank_you")  # thank_you.mp3 / .wav / .ogg
    if path is None:
        print("[SFX] thank_you 파일을 찾지 못함")
        return
    try:
        s = pygame.mixer.Sound(path)
        s.set_volume(volume)
        s.play()  # ✅ 한 번만
    except Exception as e:
        print("thank_you 재생 오류:", e)

# ----------------------------
# [시작 화면]
# ----------------------------
def show_start_screen(screen, clock):
    # ✅ 배경 이미지 로드
    bg_path = os.path.join("asset", "ui", "starting_screen.png")
    bg_image = load_image(bg_path, (SCREEN_WIDTH, SCREEN_HEIGHT), "START BG")
    
    # ✅ 별 이미지 로드 (텍스트 양옆에 붙일 이미지)
    star_path = os.path.join("asset", "ui", "star.png")
    star_image = load_image(star_path, (45, 45), "*") 
    
    # ✅ 지정하신 픽셀 폰트 로드
    font_path = os.path.join("asset", "font", "PressStart2P-Regular.ttf")
    try:
        space_font = pygame.font.Font(font_path, 40)
    except Exception:
        space_font = get_custom_font(40, bold=True)
        
    waiting = True
    while waiting:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:  # 스페이스바 누르면 다음으로 넘어감
                    waiting = False
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                    
        screen.blit(bg_image, (0, 0))
        
        # ✅ 깜빡임 효과 (500ms 주기)
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            text_img = space_font.render("PRESS SPACE KEY TO START", True, WHITE)
            
            # 중앙 위치 설정 (y좌표는 화면 하단에서 120px 위)
            text_rect = text_img.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 120))
            
            # (선택) 글자가 배경에 묻히지 않도록 약간의 검은색 그림자 효과 추가
            shadow_img = space_font.render("PRESS SPACE KEY TO START", True, BLACK)
            shadow_rect = shadow_img.get_rect(center=(SCREEN_WIDTH // 2 + 4, SCREEN_HEIGHT - 120 + 4))
            screen.blit(shadow_img, shadow_rect)
            
            # 글자 그리기
            screen.blit(text_img, text_rect)
            
            # ✅ 텍스트 양옆에 별 이미지 배치 (간격 40px)
            star_padding = 40
            left_star_rect = star_image.get_rect(center=(text_rect.left - star_padding, text_rect.centery))
            right_star_rect = star_image.get_rect(center=(text_rect.right + star_padding, text_rect.centery))
            
            # 별 그리기
            screen.blit(star_image, left_star_rect)
            screen.blit(star_image, right_star_rect)
            
        pygame.display.flip()
def show_intro_video(screen, clock):
    video_path = os.path.join("asset", "intro", "sample.mp4")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"오류: 비디오 파일을 열 수 없습니다: {video_path}")
        return

    vid_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    vid_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    vid_fps = cap.get(cv2.CAP_PROP_FPS)
    if vid_fps <= 0: vid_fps = 30 # 기본 프레임
    
    # HUD 영역을 포함한 전체 화면 기준 중앙 정렬
    pos_x = (SCREEN_WIDTH - vid_w) // 2
    pos_y = 0

    text = "평화로운 동물마을, 요즘 응급환자에 대한 뉴스가 많아지고 있어!"
    char_idx = 0.0
    dialog_font = get_custom_font(36, bold=True)
    
    waiting = True
    while waiting:
        dt = clock.tick(vid_fps) / 1000.0 # 영상 원본 속도에 맞게 프레임 고정
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # 스페이스바, 엔터, ESC 누르면 영상 스킵
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                    waiting = False

        ret, frame = cap.read()
        if not ret:
            waiting = False # 영상이 끝나면 루프 종료
            break
            
        # OpenCV(BGR)를 Pygame(RGB) 표면으로 변환
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = np.rot90(frame)
        frame = np.flipud(frame)
        video_surface = pygame.surfarray.make_surface(frame)

        # 배경 채우기 (여백 남색)
        screen.fill((25, 30, 40))
        
        # 중앙에 영상 그리기
        screen.blit(video_surface, (pos_x, pos_y))

        # 자막 타이핑 진행 (튜토리얼과 동일한 속도)
        if char_idx < len(text):
            char_idx += dt * 45.0
        
        # 하단 자막 상자 그리기 (HUD 폭까지 끝까지 길게)
        subtitle_height = 3 * TILE_SIZE
        
        # 시작 X좌표를 pos_x로, 너비를 vid_w로 설정합니다.
        subtitle_rect = pygame.Rect(pos_x, SCREEN_HEIGHT - subtitle_height, vid_w, subtitle_height)
        pygame.draw.rect(screen, (40, 50, 65), subtitle_rect)
        pygame.draw.rect(screen, WHITE, subtitle_rect, 4)

        current_text = text[:int(char_idx)]
        
        # 텍스트의 시작 X좌표도 상자 시작점(pos_x)에서 50픽셀 띄운 위치로 맞춰줍니다.
        text_start_x = pos_x + 50
        text_start_y = SCREEN_HEIGHT - subtitle_height + 40
        draw_text(screen, current_text, dialog_font, WHITE, text_start_x, text_start_y)

        pygame.display.flip()

    cap.release()
# ==========================================
# [엔딩 영상 화면]
# ==========================================
def show_outro_video(screen, clock):
    # ==================================================
    # [엔딩 데이터 설정]
    # filename(영상)  /  text(자막)  /  bgm_key(재생할 사운드 파일 base name)
    # ==================================================
    outro_data = [
        ("outro_1.mp4", "오늘처럼 우리가 함께 노력한다면 응급차가 제때 도착할 수 있을 거야!", "Ending1Sound"),
        ("outro_2.mp4", "응급 헬기도 뜰 수 있고..! 병원에서도 빠르게 진찰 받을 수 있어!", "Ending2Sound")
    ]

    dialog_font = get_custom_font(36, bold=True)

    for filename, text, bgm_key in outro_data:
        video_path = os.path.join("asset", "outro", filename)
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            print(f"오류: 비디오 파일을 열 수 없습니다: {video_path}")
            continue

        vid_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        vid_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        vid_fps = cap.get(cv2.CAP_PROP_FPS)
        if vid_fps <= 0:
            vid_fps = 30

        pos_x = (SCREEN_WIDTH - vid_w) // 2
        pos_y = 0

        # ✅ 여기서부터: 영상 오디오 대신 asset/bgm의 Ending 사운드 재생
        stop_bgm()  # 혹시 남아있는 BGM 정리
        bgm_base = os.path.join("asset", "bgm")
        bgm_path = _find_sound_file(bgm_base, bgm_key)
        if bgm_path is None:
            print(f"[BGM] {bgm_key} 파일을 찾지 못함: {os.path.join(bgm_base, bgm_key)}(.mp3/.wav/.ogg)")
        else:
            try:
                pygame.mixer.music.load(bgm_path)
                pygame.mixer.music.set_volume(0.8)
                pygame.mixer.music.play(loops=0)  # 필요하면 -1(루프) 말고 0(1회)로 바꿔도 됨
            except Exception as e:
                print(f"[{bgm_key}] 오디오 재생 실패:", e)

        char_idx = 0.0
        video_surface = None
        video_ended = False
        waiting_for_next = True

        while waiting_for_next:
            dt = clock.tick(vid_fps) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        pygame.mixer.music.stop()  # ✅ 다음 영상으로 넘어갈 때 소리 끄기
                        waiting_for_next = False
                    elif event.key == pygame.K_ESCAPE:
                        pygame.mixer.music.stop()  # ✅ 전체 스킵 시 소리 끄기
                        cap.release()
                        return

            if not video_ended:
                ret, frame = cap.read()
                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = np.rot90(frame)
                    frame = np.flipud(frame)
                    video_surface = pygame.surfarray.make_surface(frame)
                else:
                    video_ended = True

            screen.fill((25, 30, 40))
            if video_surface:
                screen.blit(video_surface, (pos_x, pos_y))

            if char_idx < len(text):
                char_idx += dt * 50.0

            subtitle_height = 3 * TILE_SIZE
            subtitle_rect = pygame.Rect(pos_x, SCREEN_HEIGHT - subtitle_height, vid_w, subtitle_height)
            pygame.draw.rect(screen, (40, 50, 65), subtitle_rect)
            pygame.draw.rect(screen, WHITE, subtitle_rect, 4)

            current_text = text[:int(char_idx)]
            lines = current_text.split('\n')

            text_start_x = pos_x + 50
            text_start_y = SCREEN_HEIGHT - subtitle_height + 40

            for i, line in enumerate(lines):
                draw_text(screen, line, dialog_font, WHITE, text_start_x, text_start_y + i * 45)

            if char_idx >= len(text):
                if (pygame.time.get_ticks() // 500) % 2 == 0:
                    prompt_font = get_custom_font(24)
                    prompt_x = pos_x + vid_w - 40
                    prompt_y = SCREEN_HEIGHT - 30
                    draw_text(screen, "▶ [SPACE] 다음 영상", prompt_font, YELLOW, prompt_x, prompt_y, align="bottomright")

            pygame.display.flip()

        pygame.mixer.music.stop()  # ✅ 영상 하나 완전히 끝날 때도 소리 끄기
        cap.release()

# ==========================================
# [엔딩 크레딧 화면] (전체 화면 재생)
# ==========================================
def show_ending_credit(screen, clock):
    video_path = os.path.join("asset", "outro", "ending_credit.mp4")
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"오류: 비디오 파일을 열 수 없습니다: {video_path}")
        return

    vid_fps = cap.get(cv2.CAP_PROP_FPS)
    if vid_fps <= 0:
        vid_fps = 30

    # ✅ 크레딧 전용 BGM: asset/bgm/Ending3Sound 재생
    stop_bgm()
    bgm_base = os.path.join("asset", "bgm")
    bgm_path = _find_sound_file(bgm_base, "Ending3Sound")
    if bgm_path is None:
        print(f"[BGM] Ending3Sound 파일을 찾지 못함: {os.path.join(bgm_base, 'Ending3Sound')}(.mp3/.wav/.ogg)")
    else:
        try:
            pygame.mixer.music.load(bgm_path)
            pygame.mixer.music.set_volume(0.8)
            pygame.mixer.music.play(loops=0)  # 필요하면 0(1회)로 변경
        except Exception as e:
            print("[Ending3Sound] 오디오 재생 실패:", e)

    video_surface = None
    video_ended = False
    waiting_for_next = True
    prompt_font = get_custom_font(24)

    while waiting_for_next:
        dt = clock.tick(vid_fps) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                    pygame.mixer.music.stop()
                    waiting_for_next = False

        if not video_ended:
            ret, frame = cap.read()
            if ret:
                frame = cv2.resize(frame, (SCREEN_WIDTH, SCREEN_HEIGHT))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = np.rot90(frame)
                frame = np.flipud(frame)
                video_surface = pygame.surfarray.make_surface(frame)
            else:
                video_ended = True

        screen.fill(BLACK)

        if video_surface:
            screen.blit(video_surface, (0, 0))

        if video_ended:
            if (pygame.time.get_ticks() // 500) % 2 == 0:
                draw_text(screen, "▶ 아무 키나 눌러 다음으로", prompt_font, YELLOW,
                          SCREEN_WIDTH - 40, SCREEN_HEIGHT - 30, align="bottomright")

        pygame.display.flip()

    pygame.mixer.music.stop()
    cap.release()

# ==========================================
# [재시작 팝업 화면]
# ==========================================
def show_restart_popup(screen, clock):
    title_font = get_custom_font(60, bold=True)
    prompt_font = get_custom_font(40)
    
    # 반투명 검은색 배경 덮기
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    
    box_w, box_h = 800, 400
    box_rect = pygame.Rect((SCREEN_WIDTH - box_w)//2, (SCREEN_HEIGHT - box_h)//2, box_w, box_h)
    
    # 이전 이벤트(스페이스바 연타 등) 비우기
    pygame.event.clear()
    
    waiting = True
    while waiting:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT"
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    return "RESTART"
                elif event.key == pygame.K_ESCAPE:
                    return "QUIT"
        
        screen.blit(overlay, (0, 0))
        pygame.draw.rect(screen, (40, 50, 65), box_rect, border_radius=20)
        pygame.draw.rect(screen, WHITE, box_rect, 4, border_radius=20)
        
        draw_text(screen, "모든 구조 임무 완료!", title_font, YELLOW, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 80, align="center")
        draw_text(screen, "게임을 처음부터 다시 시작하시겠습니까?", prompt_font, WHITE, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 10, align="center")
        
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            draw_text(screen, "[ENTER] 재시작  /  [ESC] 게임 종료", prompt_font, GREEN, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 120, align="center")
        else:
            draw_text(screen, "[ENTER] 재시작  /  [ESC] 게임 종료", prompt_font, WHITE, SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 120, align="center")
            
        pygame.display.flip()
# ----------------------------
# [이름 입력 화면] (한글 지원 버전)
# ----------------------------
def get_user_name(screen, clock):
    title_font = get_custom_font(80, bold=True)
    prompt_font = get_custom_font(40)
    name_font = get_custom_font(60, bold=True)

    user_name = ""       # 확정된 글자 (예: 안녕)
    composition = ""     # 조합 중인 글자 (예: ㅎ+ㅏ=하)
    
    input_active = True
    cursor_timer = 0
    show_cursor = True

    # 한글 입력을 받기 위해 IME 시작
    pygame.key.start_text_input()
    
    # 키 반복 입력 설정 (백스페이스 꾹 눌렀을 때 계속 지워지도록)
    pygame.key.set_repeat(500, 50)

    while input_active:
        dt = clock.tick(FPS)
        cursor_timer += dt
        if cursor_timer >= 500:
            show_cursor = not show_cursor
            cursor_timer = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            # 1. 글자 조합 중일 때 (예: 'ㄱ', '가', '강')
            elif event.type == pygame.TEXTEDITING:
                composition = event.text

            # 2. 글자가 확정되었을 때 (조합 완료)
            elif event.type == pygame.TEXTINPUT:
                if len(user_name) < 10: # 최대 글자수 제한
                    user_name += event.text
                composition = "" # 확정되었으므로 조합 초기화

            # 3. 특수 키 처리 (엔터, 백스페이스, ESC)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                
                elif event.key == pygame.K_RETURN:
                    # 조합 중인 글자가 없고, 입력된 이름이 있을 때만 종료
                    if not composition and len(user_name.strip()) > 0:
                        input_active = False
                
                elif event.key == pygame.K_BACKSPACE:
                    # 조합 중인 글자가 없을 때만 뒤에서 한 글자 삭제
                    # (조합 중일 때는 IME가 알아서 자소 단위로 지워줌)
                    if not composition and len(user_name) > 0:
                        user_name = user_name[:-1]

        screen.fill((20, 25, 35))
        draw_text(screen, "Golden Time", title_font, RED, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 150, "center")
        draw_text(screen, "구조대원 이름을 입력하세요", prompt_font, WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20, "center")

        input_box = pygame.Rect(SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 + 50, 400, 80)
        pygame.draw.rect(screen, (40, 50, 70), input_box, border_radius=10)
        pygame.draw.rect(screen, WHITE, input_box, 3, border_radius=10)

        # 보여줄 이름 = 확정된 이름 + 조합 중인 이름 + 커서
        display_name = user_name + composition + ("|" if show_cursor else "")
        
        draw_text(screen, display_name, name_font, YELLOW, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 90, "center")
        draw_text(screen, "입력 후 ENTER를 누르세요", prompt_font, GRAY, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 200, "center")
        pygame.display.flip()
    
    # 입력 종료 후 IME 끄기
    pygame.key.stop_text_input()
    
    # 최종적으로 조합 중이던 글자까지 합쳐서 반환
    return (user_name + composition).strip()
# ----------------------------
# [스테이지 2 팝업 화면]
# ----------------------------
def show_stage2_popup(screen, clock):
    # ✅ 팝업 배경 이미지 로드
    bg_path = os.path.join("asset", "ui", "stage2_popup.png")
    bg_image = load_image(bg_path, (SCREEN_WIDTH, SCREEN_HEIGHT), "STAGE2 POPUP")
    
    # ✅ 지정하신 픽셀 폰트 로드
    font_path = os.path.join("asset", "font", "PressStart2P-Regular.ttf")
    try:
        space_font = pygame.font.Font(font_path, 30) # 폰트 크기
    except Exception:
        space_font = get_custom_font(30, bold=True)
        
    waiting = True
    while waiting:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:  # 스페이스바 누르면 다음(Stage 2)으로 넘어감
                    waiting = False
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                    
        screen.blit(bg_image, (0, 0))
        
        # ✅ 깜빡임 효과 (500ms 주기)
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            text_color = BLACK
            shadow_color = WHITE
            
            text_img = space_font.render("PRESS SPACE KEY TO START", True, text_color)
            shadow_img = space_font.render("PRESS SPACE KEY TO START", True, shadow_color)
            
            # 하단 베이지색 영역 위치 지정 (필요 시 조절)
            y_pos = SCREEN_HEIGHT - 150
            
            text_rect = text_img.get_rect(center=(SCREEN_WIDTH // 2, y_pos))
            shadow_rect = shadow_img.get_rect(center=(SCREEN_WIDTH // 2 + 3, y_pos + 3))
            
            # 그림자 먼저 그리고 글자를 그 위에 얹음
            screen.blit(shadow_img, shadow_rect)
            screen.blit(text_img, text_rect)
            
        pygame.display.flip()
# ==========================================
# 👇 여기서부터 아래 코드 전체를 복사해서 덮어씌워 주세요!
# ==========================================
# ==========================================
# [인트로 영상 화면 + seq1sound~seq7sound BGM]
# ==========================================
def show_intro_video(screen, clock):
    # ==================================================
    # [인트로 데이터 설정]
    # filename(영상) / text(자막) / bgm_key(사운드 파일 base name)
    # ==================================================
    intro_data = [
        ("intro_1.mp4", "평화로운 동물마을, 요즘 응급환자에 대한 뉴스가 많아지고 있어!", "seq1sound"),
        ("intro_2.mp4", "마침! 응급상황이 발생했어!", "seq2sound"),
        ("intro_3.mp4", "이런, 차가 막히고 있어. \n비켜주지 않는 차 때문에 이동이 어려워.", "seq3sound"),
        ("intro_4.mp4", "가끔 도로 공사로 길이 막히기도 해. \n빨리 피해갈 방법을 찾아야겠어.", "seq4sound"),
        ("intro_5.mp4", "응급 구조를 기다리는 아파하는 환자들..", "seq5sound"),
        ("intro_6.mp4", "나는 초보 구급차야. 나를 도와줄 수 있을까?", "seq6sound"),
        ("intro_7.mp4", "네가 도와준다니 정말 고마워! \n주어진 시간안에 최대한 많은 환자를 구조해줘!", "seq7sound"),
    ]

    dialog_font = get_custom_font(36, bold=True)

    for filename, text, bgm_key in intro_data:
        video_path = os.path.join("asset", "intro", filename)
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            print(f"오류: 비디오 파일을 열 수 없습니다: {video_path}")
            continue

        vid_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        vid_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        vid_fps = cap.get(cv2.CAP_PROP_FPS)
        if vid_fps <= 0:
            vid_fps = 30

        pos_x = (SCREEN_WIDTH - vid_w) // 2
        pos_y = 0

        # ✅ 여기서부터: 영상마다 seq 사운드 재생
        stop_bgm()  # 이전 seq가 남아있으면 정리
        bgm_base = os.path.join("asset", "bgm")
        bgm_path = _find_sound_file(bgm_base, bgm_key)
        if bgm_path is None:
            print(f"[BGM] {bgm_key} 파일을 찾지 못함: {os.path.join(bgm_base, bgm_key)}(.mp3/.wav/.ogg)")
        else:
            try:
                pygame.mixer.music.load(bgm_path)
                pygame.mixer.music.set_volume(0.8)
                pygame.mixer.music.play(loops=0)  # ✅ 1회 재생
            except Exception as e:
                print(f"[{bgm_key}] 오디오 재생 실패:", e)

        char_idx = 0.0
        video_surface = None
        video_ended = False
        waiting_for_next = True

        while waiting_for_next:
            dt = clock.tick(vid_fps) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        # ✅ 다음 영상으로 넘어갈 때 소리 끄기
                        pygame.mixer.music.stop()
                        waiting_for_next = False
                    elif event.key == pygame.K_ESCAPE:
                        # ✅ 인트로 전체 스킵 시 소리 끄기
                        pygame.mixer.music.stop()
                        cap.release()
                        return

            if not video_ended:
                ret, frame = cap.read()
                if ret:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = np.rot90(frame)
                    frame = np.flipud(frame)
                    video_surface = pygame.surfarray.make_surface(frame)
                else:
                    video_ended = True

            screen.fill((25, 30, 40))
            if video_surface:
                screen.blit(video_surface, (pos_x, pos_y))

            if char_idx < len(text):
                char_idx += dt * 50.0

            subtitle_height = 3 * TILE_SIZE
            subtitle_rect = pygame.Rect(pos_x, SCREEN_HEIGHT - subtitle_height, vid_w, subtitle_height)
            pygame.draw.rect(screen, (40, 50, 65), subtitle_rect)
            pygame.draw.rect(screen, WHITE, subtitle_rect, 4)

            current_text = text[:int(char_idx)]
            lines = current_text.split('\n')

            text_start_x = pos_x + 50
            text_start_y = SCREEN_HEIGHT - subtitle_height + 40

            for i, line in enumerate(lines):
                draw_text(screen, line, dialog_font, WHITE, text_start_x, text_start_y + i * 45)

            if char_idx >= len(text):
                if (pygame.time.get_ticks() // 500) % 2 == 0:
                    prompt_font = get_custom_font(24)
                    prompt_x = pos_x + vid_w - 40
                    prompt_y = SCREEN_HEIGHT - 30
                    draw_text(screen, "▶ [SPACE] 다음 영상", prompt_font, YELLOW, prompt_x, prompt_y, align="bottomright")

            pygame.display.flip()

        # ✅ 영상 하나 완전히 끝날 때도 소리 정리
        pygame.mixer.music.stop()
        cap.release()

    # 인트로 7개 끝나면 혹시 남은 소리 정리
    stop_bgm()
# ----------------------------
# [게임 클래스]
# ----------------------------
class Ambulance(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        
        self.car_images = {
            "up": load_image(os.path.join("asset", "car", "user_car_up.png"), (TILE_SIZE, TILE_SIZE), "UP"),
            "down": load_image(os.path.join("asset", "car", "user_car_down.png"), (TILE_SIZE, TILE_SIZE), "DOWN"),
            "left": load_image(os.path.join("asset", "car", "user_car_left.png"), (TILE_SIZE, TILE_SIZE), "LEFT"),
            "right": load_image(os.path.join("asset", "car", "user_car_right.png"), (TILE_SIZE, TILE_SIZE), "RIGHT")
        }

        self.heli_images = {
            "up": load_image(os.path.join("asset", "heli", "user_heli_up.png"), (TILE_SIZE, TILE_SIZE), "H_UP"),
            "down": load_image(os.path.join("asset", "heli", "user_heli_down.png"), (TILE_SIZE, TILE_SIZE), "H_DOWN"),
            "left": load_image(os.path.join("asset", "heli", "user_heli_left.png"), (TILE_SIZE, TILE_SIZE), "H_LEFT"),
            "right": load_image(os.path.join("asset", "heli", "user_heli_right.png"), (TILE_SIZE, TILE_SIZE), "H_RIGHT")
        }
        
        self.direction = "right"
        self.is_heli = False
        self.image = self.heli_images[self.direction] if self.is_heli else self.car_images[self.direction]
        
        self.rect = self.image.get_rect()
        self.grid_x, self.grid_y = x, y
        self.pixel_x, self.pixel_y = x * TILE_SIZE, y * TILE_SIZE
        self.target_x, self.target_y = self.pixel_x, self.pixel_y
        self.move_speed = 12
        self.is_moving = False
        self.rect.topleft = (self.pixel_x, self.pixel_y)
        self.has_patient = False

    def update(self):
        if self.is_moving:
            if self.pixel_x < self.target_x:
                self.pixel_x += self.move_speed
            elif self.pixel_x > self.target_x:
                self.pixel_x -= self.move_speed
            if self.pixel_y < self.target_y:
                self.pixel_y += self.move_speed
            elif self.pixel_y > self.target_y:
                self.pixel_y -= self.move_speed

            if abs(self.pixel_x - self.target_x) < self.move_speed and abs(self.pixel_y - self.target_y) < self.move_speed:
                self.pixel_x, self.pixel_y = self.target_x, self.target_y
                self.is_moving = False
            self.rect.topleft = (self.pixel_x, self.pixel_y)

    def move(self, dx, dy, obstacles, current_map=MAP_DATA):
        if self.is_moving:
            return
            
        if dx == -1: self.direction = "left"
        elif dx == 1: self.direction = "right"
        elif dy == -1: self.direction = "up"
        elif dy == 1: self.direction = "down"
            
        self.image = self.heli_images[self.direction] if self.is_heli else self.car_images[self.direction]

        next_x, next_y = self.grid_x + dx, self.grid_y + dy
        
        if next_y < 0 or next_y >= len(current_map) or next_x < 0 or next_x >= len(current_map[0]):
            return
            
        if not self.is_heli:
            if current_map[next_y][next_x] == 0:
                return
            for obs in obstacles:
                if obs.grid_x == next_x and obs.grid_y == next_y:
                    return
                
        self.grid_x, self.grid_y = next_x, next_y
        self.target_x, self.target_y = next_x * TILE_SIZE, next_y * TILE_SIZE
        self.is_moving = True


class Patient(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.is_fake = random.random() < 0.3
        self.spawn_location()

    def spawn_location(self):
        house_coords = [(x, y) for y in range(len(MAP_DATA)) for x in range(len(MAP_DATA[0])) if MAP_DATA[y][x] == 3]
        if house_coords:
            self.grid_x, self.grid_y = random.choice(house_coords)
            self.rect.topleft = (self.grid_x * TILE_SIZE, self.grid_y * TILE_SIZE)


class Obstacle(pygame.sprite.Sprite):
    def __init__(self, player_x, player_y):
        super().__init__()
        
        obstacle_paths = [
            os.path.join("asset", "obstacle", "obstacle_acci.png"),
            os.path.join("asset", "obstacle", "obstacle_angry_car.png")
        ]
        
        chosen_path = random.choice(obstacle_paths)
        self.image = load_image(chosen_path, (TILE_SIZE, TILE_SIZE), "OBS")
        
        self.rect = self.image.get_rect()
        self.spawn_location(player_x, player_y)

    def spawn_location(self, px, py):
        road_coords = [(x, y) for y in range(len(MAP_DATA)) for x in range(len(MAP_DATA[0]))
                       if MAP_DATA[y][x] == 1 and not (x == px and y == py)]
        if road_coords:
            self.grid_x, self.grid_y = random.choice(road_coords)
            self.rect.topleft = (self.grid_x * TILE_SIZE, self.grid_y * TILE_SIZE)


class HeliCoin(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        path = os.path.join("asset", "heli", "item_helicoin.png")
        self.image = load_image(path, (TILE_SIZE, TILE_SIZE), "COIN")
        self.rect = self.image.get_rect()
        self.grid_x, self.grid_y = -1, -1
        self.active = False
        self.rect.topleft = (-1000, -1000)

    def spawn(self, player, obstacles):
        obs_coords = {(o.grid_x, o.grid_y) for o in obstacles}
        road_coords = [(x, y) for y in range(len(MAP_DATA)) for x in range(len(MAP_DATA[0]))
                       if MAP_DATA[y][x] == 1 and (x, y) not in obs_coords and not (x == player.grid_x and y == player.grid_y)]
        
        if road_coords:
            self.grid_x, self.grid_y = random.choice(road_coords)
            self.rect.topleft = (self.grid_x * TILE_SIZE, self.grid_y * TILE_SIZE)
            self.active = True

    def hide(self):
        self.active = False
        self.grid_x, self.grid_y = -1, -1
        self.rect.topleft = (-1000, -1000)


def check_path_exists(start_x, start_y, target_x, target_y, obstacles_group):
    obstacle_coords = {(obs.grid_x, obs.grid_y) for obs in obstacles_group}
    visited = {(start_x, start_y)}
    queue = [(start_x, start_y)]

    while queue:
        cx, cy = queue.pop(0)
        if cx == target_x and cy == target_y:
            return True
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = cx + dx, cy + dy
            if 0 <= ny < len(MAP_DATA) and 0 <= nx < len(MAP_DATA[0]):
                if MAP_DATA[ny][nx] != 0 and (nx, ny) not in obstacle_coords and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    queue.append((nx, ny))
    return False


def generate_safe_obstacles(count, player, patient):
    while True:
        temp_obstacles = pygame.sprite.Group()
        for _ in range(count):
            temp_obstacles.add(Obstacle(player.grid_x, player.grid_y))
        if check_path_exists(player.grid_x, player.grid_y, patient.grid_x, patient.grid_y, temp_obstacles):
            return temp_obstacles

def respawn_patient_and_shuffle_hospitals(stage, all_sprites):
    p = Patient()   
    all_sprites.add(p)

    if stage == 2:
        return p, pick_active_hospitals(stage)
    else:
        return p, None


# ----------------------------
# [HUD 클래스] 
# ----------------------------
class GoldenTimeHUD408x1080:
    def __init__(self, user_name="대원"):
        self.W, self.H = HUD_WIDTH, HUD_HEIGHT
        self.rect = pygame.Rect(0, 0, self.W, self.H)
        self.user_name = user_name

        self.title_font = get_custom_font(44, bold=True)
        self.h1_font = get_custom_font(34, bold=True)
        self.h2_font = get_custom_font(26, bold=True)
        self.small_font = get_custom_font(18)
        self.fail_font = get_custom_font(40, bold=True)

        self.stage = 1 
        self.stage_time_left = 10.0
        self.golden_time_left = 10.0
        self.saved_count = 0
        self.status_text = "구조 대기 중"
        self.golden_running = False
        self.fail_banner_left = 0.0
        self.is_complete = False
        self.animal_pop_t = 0.0
        self._beat_phase = 0.0

        base = os.path.join("asset", "ui")
        if not os.path.exists(base):
            os.makedirs(base, exist_ok=True)

        self.heart_img = load_image(os.path.join(base, "heart.png"), (110, 110))
        self.animal_frames = [load_image(os.path.join(base, f"animal_{i}.png"), (120, 120), f"A{i}") for i in range(1, 9)]
        self.animal_fallback = load_image(os.path.join(base, "animal.png"), (120, 120), "Animal")
        self.animal_index = 0
        
        kb_base = os.path.join("asset", "keyboard")
        if not os.path.exists(kb_base):
            os.makedirs(kb_base, exist_ok=True)

        self.key_imgs = {
            "up": (
                load_image(os.path.join(kb_base, "uparrow.png"), (74, 74), "↑"),
                load_image(os.path.join(kb_base, "uparrow2.png"), (74, 74), "↑")
            ),
            "down": (
                load_image(os.path.join(kb_base, "downarrow.png"), (74, 74), "↓"),
                load_image(os.path.join(kb_base, "downarrow2.png"), (74, 74), "↓")
            ),
            "left": (
                load_image(os.path.join(kb_base, "leftarrow.png"), (74, 74), "←"),
                load_image(os.path.join(kb_base, "leftarrow2.png"), (74, 74), "←")
            ),
            "right": (
                load_image(os.path.join(kb_base, "rightarrow.png"), (74, 74), "→"),
                load_image(os.path.join(kb_base, "rightarrow2.png"), (74, 74), "→")
            ),
            "space": (
                load_image(os.path.join(kb_base, "spacebar.png"), (260, 70), "SPACE"),
                load_image(os.path.join(kb_base, "spacebar2.png"), (260, 70), "SPACE")
            ),
        }

    def get_current_animal_surface(self) -> pygame.Surface:
        if 0 <= self.animal_index < len(self.animal_frames):
            return self.animal_frames[self.animal_index]
        return self.animal_fallback

    def update(self, dt, stage, stage_time_left, golden_time_left, saved_count,
               golden_running, fail_banner_left, status_text, stage_running,
               is_complete, animal_index, animal_pop_t):
        self.stage = stage
        self.stage_time_left = stage_time_left
        self.golden_time_left = golden_time_left
        self.saved_count = saved_count
        self.golden_running = golden_running
        self.fail_banner_left = fail_banner_left
        self.status_text = status_text
        self.is_complete = is_complete
        self.animal_index = animal_index
        self.animal_pop_t = animal_pop_t
        if stage_running:
            self._beat_phase += dt * 6.0

    def draw(self, screen: pygame.Surface):
        screen.fill((27, 35, 66))
        pygame.draw.rect(screen, (70, 80, 110), self.rect, 2)
        pad = 24
        x0 = pad
        y = 24
        draw_text(screen, "Golden Time", self.title_font, (245, 220, 120), self.W // 2, y, "midtop")
        y += 60
        draw_text(screen, f"대원: {self.user_name}", self.h2_font, (180, 255, 180), self.W // 2, y, "midtop")
        y += 40
        pygame.draw.line(screen, (70, 80, 110), (x0, y), (self.W - pad, y), 2)
        y += 22
        if self.stage == "TUTORIAL":
            draw_text(screen, "TUTORIAL", self.h1_font, (235, 240, 250), x0, y, "topleft")
        else:
            draw_text(screen, f"STAGE  {self.stage}", self.h1_font, (235, 240, 250), x0, y, "topleft")
        y += 58
        # ------------------------------------------------
        
        draw_text(screen, "스테이지 남은 시간", self.small_font, (170, 180, 200), x0, y, "topleft")
        y += 26
        draw_text(screen, format_time(self.stage_time_left), self.h1_font, WHITE, x0, y, "topleft")
        y += 60
        draw_text(screen, "환자 골든타임(제한)", self.small_font, (170, 180, 200), x0, y, "topleft")
        y += 26

        base_color = (255, 90, 90) if self.golden_time_left <= 3 else (255, 200, 90) if self.golden_time_left <= 6 else (120, 255, 160)
        show_timer = True
        if self.golden_running and self.golden_time_left <= 3:
            show_timer = ((pygame.time.get_ticks() // 250) % 2 == 0)

        if show_timer:
            draw_text(screen, format_time(self.golden_time_left), self.h1_font, base_color, x0, y, "topleft")
        else:
            draw_text(screen, "  ", self.h1_font, base_color, x0, y, "topleft")
        y += 60

        draw_text(screen, "구한 환자", self.small_font, (170, 180, 200), x0, y, "topleft")
        y += 26
        draw_text(screen, f"{self.saved_count} 명", self.h1_font, (235, 240, 250), x0, y, "topleft")
        y += 70

        box_h = 180
        box = pygame.Rect(x0, y, self.W - pad - x0, box_h)
        pygame.draw.rect(screen, (26, 28, 40), box, border_radius=16)
        pygame.draw.rect(screen, (70, 80, 110), box, 2, border_radius=16)

        beat = 1.0 + 0.10 * (1 + math.sin(self._beat_phase))
        hw, hh = self.heart_img.get_size()
        heart_scaled = pygame.transform.smoothscale(self.heart_img, (int(hw * beat), int(hh * beat)))
        screen.blit(heart_scaled, (box.x + 3, box.y + 14))

        animal = self.get_current_animal_surface()
        ay = box.y + 20
        if self.animal_pop_t > 0:
            t = max(0.0, min(1.0, self.animal_pop_t / 0.35))
            scale = 1.0 + 0.18 * t
            nw, nh = int(animal.get_width() * scale), int(animal.get_height() * scale)
            animal_scaled = pygame.transform.smoothscale(animal, (nw, nh))
            screen.blit(animal_scaled, animal_scaled.get_rect(center=(box.centerx, ay + animal.get_height() // 2)))
        else:
            screen.blit(animal, (box.centerx - animal.get_width() // 2, ay))

        draw_text(screen, self.status_text, self.h2_font, (210, 220, 240), box.centerx, box.bottom - 18, "midbottom")

        if self.fail_banner_left > 0:
            overlay = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            screen.blit(overlay, (box.x, box.y))
            draw_text(screen, "FAIL!", self.fail_font, (255, 80, 80), box.centerx, box.centery, "center")

        y += box_h + 50

        draw_text(screen, "조작키", self.h2_font, (235, 240, 250), x0, y, "topleft")
        y += 44
        keys = pygame.key.get_pressed()
        pressed = {
            "up": keys[pygame.K_UP], "down": keys[pygame.K_DOWN],
            "left": keys[pygame.K_LEFT], "right": keys[pygame.K_RIGHT], "space": keys[pygame.K_SPACE]
        }

        k_center_x = self.W // 2
        ky = y
        up_img = self.key_imgs["up"][1 if pressed["up"] else 0]
        screen.blit(up_img, up_img.get_rect(midtop=(k_center_x, ky)))
        ky += 82

        left_img = self.key_imgs["left"][1 if pressed["left"] else 0]
        down_img = self.key_imgs["down"][1 if pressed["down"] else 0]
        right_img = self.key_imgs["right"][1 if pressed["right"] else 0]

        gap = 10
        total_w = left_img.get_width() + down_img.get_width() + right_img.get_width() + gap * 2
        start_x = k_center_x - total_w // 2
        screen.blit(left_img, (start_x, ky))
        screen.blit(down_img, (start_x + left_img.get_width() + gap, ky))
        screen.blit(right_img, (start_x + left_img.get_width() + gap + down_img.get_width() + gap, ky))

        ky += 100
        space_img = self.key_imgs["space"][1 if pressed["space"] else 0]
        screen.blit(space_img, space_img.get_rect(midtop=(k_center_x, ky)))


# ----------------------------
# [메인 실행] 통합 로직
# ----------------------------
def main():
    pygame.init()
    init_audio()
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Ambulance Rush - 1920x1080")
    clock = pygame.time.Clock()

    play_bgm("start_screen")
    show_start_screen(screen, clock)
    stop_bgm()
    
    show_intro_video(screen, clock)

    user_name = get_user_name(screen, clock)
    if not user_name:
        user_name = "무명 대원"

    font = get_custom_font(30)
    dialog_font = get_custom_font(36, bold=True)

  # ✅ Stage별 결과창 배경 이미지
    result_stage1_bg_path = os.path.join("asset", "ui", "result_stage1.png")  # <- stage1 결과창
    result_bg_path = os.path.join("asset", "ui", "result_bg.png")            # <- stage2 결과창(기존 유지)

    game_state = "TUTORIAL"
    play_bgm("tutorial")

    # ==========================================
    # [튜토리얼 전용 객체 및 진행 상태 세팅]
    # ==========================================
    tut_player = Ambulance(0, 4) # 시작 위치 변경 (제일 왼쪽 아래 도로)

    tut_patient = Patient()
    tut_patient.grid_x, tut_patient.grid_y = 5, 5 # 튜토리얼용 환자 위치 (한 칸 내림)
    tut_patient.rect.topleft = (5 * TILE_SIZE, 5 * TILE_SIZE)
    tut_patient.is_fake = False # 튜토리얼은 무조건 진짜 환자

    tut_obstacle = Obstacle(0, 0)
    tut_obstacle.grid_x, tut_obstacle.grid_y = 7, 4 # 튜토리얼용 장애물 위치
    tut_obstacle.rect.topleft = (7 * TILE_SIZE, 4 * TILE_SIZE)
    tut_obstacles_group = pygame.sprite.Group(tut_obstacle)

    tut_helicoin = HeliCoin()
    tut_helicoin.grid_x, tut_helicoin.grid_y = 4, 4 # 장애물 왼쪽 교차로
    tut_helicoin.rect.topleft = (4 * TILE_SIZE, 4 * TILE_SIZE)
    tut_helicoin.active = False # 나중에 트리거 시 활성화

    tut_sprites = pygame.sprite.Group()
    tut_sprites.add(tut_player, tut_patient, tut_obstacle)

    # 튜토리얼 대화 데이터 및 타이핑 효과 변수
    # 튜토리얼 대화 데이터 및 타이핑 효과 변수
    tut_state = 0
    tut_sub_step = 0
    tut_dialogues = [
        # State 0 (시작)
        [f"{user_name}(이)가 도와준다니 정말 고마워!\n우리에게 주어진 미션은 주어진 시간 안에 최대한 많은 환자를 살리는 거야.",
         "이동은 키보드의 방향키를 사용해 봐!"],
        # State 1 (첫 이동 완료)
        ["환자를 병원으로 이송해야 해.",
         "환자를 태우기 위해서는 환자가 있는 칸에 가서 스페이스 키를 눌러봐!"],
        # State 2 (환자 탑승 완료)
        ["앗! 저게 뭐지? 가까이 다가가 볼까?"],
        # State 3 (장애물 근접)
        ["이동을 방해하는 상황이 발생했어!\n공사나 비켜주지 않는 차가 있다면 돌아가야 해.",
         "그렇지만 이동을 도와주는 특수 아이템도 있어 다가가보자!"],
        # State 4 (헬기 탑승)
        ["헬기 위에 올라타면 도로 상황과 상관없이 병원에 빠르게 도착할 수 있어.\n(방향키를 눌러 우측 끝 병원으로 날아가 보자)"],
        # State 5 (병원 도착 - 새롭게 추가된 부분!)
        ["병원에 도착했어!\n스페이스 키를 눌러 환자를 무사히 내려주자."],
        # State 6 (완료 - 기존 State 5에서 번호 변경)
        ["자 그럼 출동해볼까? (Enter 키를 눌러 실전 투입)"]
    ]
    tut_current_text = tut_dialogues[tut_state][tut_sub_step]
    tut_typed_text = ""
    tut_char_idx = 0.0

    # 튜토리얼 전용 깜빡이는 환자 건물
    tut_on_house = load_image(os.path.join("asset", "patient_on", "on_building.png"), (TILE_SIZE, TILE_SIZE), "ON_HOUSE")
    # ==========================================
    # --- [여기에 아래 두 줄을 추가해 주세요!] ---
    tut_bg_image = load_image(os.path.join("asset", "map", "tut_map.png"), (GAME_WIDTH, GAME_HEIGHT), "TUT BG")
    tut_house_off = load_image(os.path.join("asset", "patient_off", "house_blue(1,10).png"), (TILE_SIZE, TILE_SIZE), "HOUSE")

    # 맵 조각 이미지 로드 (140장)
    map_images = []
    for i in range(1, 141):
        filename = os.path.join("asset", "map", f"sliced_map_{i:02d}.png")
        img = load_image(filename, (TILE_SIZE, TILE_SIZE), f"{i}")
        map_images.append(img)

    # --- 환자 발생 시(ON) 집 이미지 로드 ---
    on_house_surfaces = {}
    for (hx, hy), filename in ON_HOUSE_IMAGES.items():
        path = os.path.join("asset", "patient_on", filename)
        on_house_surfaces[(hx, hy)] = load_image(path, (TILE_SIZE, TILE_SIZE), "ON_HOUSE")

    # --- 병원 활성/비활성 이미지 로드 ---
    hospital_active_surf = load_image(os.path.join("asset", "hospital", HOSPITAL_ACTIVE_IMG),
                                  (TILE_SIZE, TILE_SIZE), "H_ON")
    hospital_inactive_surf = load_image(os.path.join("asset", "hospital", HOSPITAL_INACTIVE_IMG),
                                    (TILE_SIZE, TILE_SIZE), "H_OFF")

    # [실전] 게임용 객체 세팅
    player = Ambulance(6, 6)  
    current_patient = Patient()
    obstacles = generate_safe_obstacles(5, player, current_patient)
    
    # 헬기 아이템 생성 및 그룹에 추가
    heli_coin = HeliCoin()
    heli_spawn_timer = random.uniform(15.0, 20.0) 
    
    all_sprites = pygame.sprite.Group()
    all_sprites.add(player, current_patient, obstacles, heli_coin)

    score = 0
    game_msg = "이동 후 스페이스바를 눌러 탑승시키세요"
    hud = GoldenTimeHUD408x1080(user_name=user_name)
    hud_state = "PATIENT_WAIT"

    # -------------------------
    # [Stage / 병원 활성 상태]
    # -------------------------
    stage = 1
    active_hospitals = pick_active_hospitals(stage)

    stage_time = 60.0
    golden_time = 15.0
    time_limit_played = False

    saved_patients = 0
    failed_patients = 0

    saved_animals = []
    failed_animals = []

    fail_banner_timer = 0.0
    complete_timer = 0.0
    animal_idx = 0
    animal_pop = 0.0
    animal_cycle_idx = 0

    game_over = False

    prank_call_timer = 0.0
    time_limit_played = False

    game_surface = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
    hud_surface = pygame.Surface((HUD_WIDTH, HUD_HEIGHT))

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                if game_state == "TUTORIAL":
                    if event.key == pygame.K_SPACE:
                        if tut_char_idx < len(tut_current_text):
                            tut_char_idx = float(len(tut_current_text))
                        else:
                            if tut_state == 0 and tut_sub_step == 0:
                                tut_sub_step += 1
                                tut_current_text = tut_dialogues[tut_state][tut_sub_step]
                                tut_char_idx = 0.0
                            elif tut_state == 1:
                                if tut_sub_step == 0:
                                    tut_sub_step += 1
                                    tut_current_text = tut_dialogues[tut_state][tut_sub_step]
                                    tut_char_idx = 0.0
                                elif tut_sub_step == 1:
                                    if tut_player.grid_x == tut_patient.grid_x and tut_player.grid_y == tut_patient.grid_y and not tut_player.has_patient:
                                        tut_player.has_patient = True
                                        tut_patient.kill()
                                        tut_state = 2
                                        tut_sub_step = 0
                                        tut_current_text = tut_dialogues[tut_state][tut_sub_step]
                                        tut_char_idx = 0.0
                            elif tut_state == 3 and tut_sub_step == 0:
                                tut_sub_step += 1
                                tut_current_text = tut_dialogues[tut_state][tut_sub_step]
                                tut_char_idx = 0.0
                                tut_helicoin.active = True
                                tut_sprites.add(tut_helicoin)
                            # --- [추가된 부분] State 5에서 스페이스바로 환자 하차 ---
                            elif tut_state == 5:
                                if tut_player.grid_x == 13 and tut_player.grid_y == 4 and tut_player.has_patient:
                                    stop_heli_loop()
                                    tut_player.is_heli = False                            
                                    tut_player.has_patient = False  # 환자 내려주기
                                    tut_state = 6                   # 다음 단계로 이동
                                    tut_sub_step = 0
                                    tut_current_text = tut_dialogues[tut_state][tut_sub_step]
                                    tut_char_idx = 0.0
                                    
                    elif event.key == pygame.K_RETURN:
                        # [수정된 부분] 마지막 단계가 State 6으로 밀렸으므로 조건을 수정합니다.
                        if tut_state == 6 and tut_sub_step == 0 and tut_char_idx >= len(tut_current_text):
                            game_state = "PLAYING"
                            stage_time = 60.0
                            golden_time = 15.0
                            time_limit_played = False
                            game_state = "PLAYING"
                            play_bgm("game_ing")  # ✅ Stage1/Stage2 공용 BGM
                            stage_time = 60.0
                            golden_time = 15.0
                            time_limit_played = False

                elif game_state == "PLAYING":
                    if event.key == pygame.K_SPACE and (not game_over) and (not player.is_moving):
                        if not player.has_patient:
                            if player.grid_x == current_patient.grid_x and player.grid_y == current_patient.grid_y:
                                if current_patient.is_fake:
                                    play_fake_tel_sound()
                                    game_msg = "장난전화!! (재배치)"
                                    prank_call_timer = 1.5
                                    current_patient.kill()
                                    current_patient, new_active = respawn_patient_and_shuffle_hospitals(stage, all_sprites)
                                    if new_active is not None:
                                        active_hospitals = new_active

                                    golden_time = 15.0
                                    time_limit_played = False
                                    hud_state = "PATIENT_WAIT"

                                    for obs in obstacles:
                                        obs.kill()
                                    obstacles = generate_safe_obstacles(5, player, current_patient)
                                    all_sprites.add(obstacles)
                                else:
                                    game_msg = "환자 탑승! 병원으로 이동 후 스페이스바!"
                                    player.has_patient = True
                                    current_patient.kill()
                                    hud_state = "RESCUING"
                            else:
                                game_msg = "주변에 환자가 없습니다!"
                        else:
                            if (player.grid_x, player.grid_y) in active_hospitals:
                                score += 100
                                game_msg = f"이송 성공! 점수: {score}"
                                player.has_patient = False
                                play_thank_you_sound()
                                
                                if player.is_heli:
                                    stop_heli_loop()
                                    player.is_heli = False
                                    player.image = player.car_images[player.direction]
                                    heli_spawn_timer = random.uniform(20.0, 30.0) 

                                hud_state = "COMPLETE"
                                complete_timer = 1.0

                                saved_patients += 1
                                saved_animals.append(ANIMAL_NAMES[animal_cycle_idx])
                                animal_cycle_idx = (animal_cycle_idx + 1) % len(ANIMAL_NAMES)

                                animal_idx = (animal_idx + 1) % 8
                                animal_pop = 0.35

                                current_patient, new_active = respawn_patient_and_shuffle_hospitals(stage, all_sprites)
                                if new_active is not None:
                                    active_hospitals = new_active

                                golden_time = 15.0
                                time_limit_played = False
                                hud_state = "PATIENT_WAIT"

                                for obs in obstacles:
                                    obs.kill()
                                obstacles = generate_safe_obstacles(5, player, current_patient)
                                all_sprites.add(obstacles)
                            else:
                                game_msg = "여기는 병원이 아닙니다!"

        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_LEFT]:
            dx = -1
        elif keys[pygame.K_RIGHT]:
            dx = 1
        elif keys[pygame.K_UP]:
            dy = -1
        elif keys[pygame.K_DOWN]:
            dy = 1

        if game_state == "TUTORIAL":
            if tut_char_idx < len(tut_current_text):
                tut_char_idx += dt * 35.0 
                tut_typed_text = tut_current_text[:int(tut_char_idx)]
            else:
                tut_typed_text = tut_current_text

            can_move = True
            if tut_state == 0 and tut_sub_step == 0: can_move = False
            if tut_state == 1 and tut_sub_step == 0: can_move = False
            if tut_state == 3 and tut_sub_step == 0: can_move = False
            if tut_state == 5: can_move = False  # 환자 내려주기 대기 중 이동 불가
            if tut_state == 6: can_move = False  # 엔터 키 대기 중 이동 불가

            if dx != 0 or dy != 0:
                if can_move:
                    tut_player.move(dx, dy, tut_obstacles_group, current_map=TUTORIAL_MAP)
                    if tut_state == 0 and tut_sub_step == 1 and tut_char_idx >= len(tut_current_text):
                        tut_state = 1
                        tut_sub_step = 0
                        tut_current_text = tut_dialogues[tut_state][tut_sub_step]
                        tut_char_idx = 0.0

            tut_player.update()

            if tut_state == 2 and tut_char_idx >= len(tut_current_text) and not tut_player.is_moving:
                if tut_player.grid_x == 6 and tut_player.grid_y == 4:
                    tut_state = 3
                    tut_sub_step = 0
                    tut_current_text = tut_dialogues[tut_state][tut_sub_step]
                    tut_char_idx = 0.0

            if tut_state == 3 and tut_sub_step == 1 and tut_helicoin.active and not tut_player.is_moving:
                if tut_player.grid_x == tut_helicoin.grid_x and tut_player.grid_y == tut_helicoin.grid_y:
                    play_item_heli_sound()
                    tut_player.is_heli = True
                    tut_player.image = tut_player.heli_images[tut_player.direction]
                    tut_helicoin.hide()
                    tut_helicoin.kill()
                    start_heli_loop()
                    tut_state = 4
                    tut_sub_step = 0
                    tut_current_text = tut_dialogues[tut_state][tut_sub_step]
                    tut_char_idx = 0.0
                    
            if tut_state == 4 and tut_char_idx >= len(tut_current_text) and not tut_player.is_moving:
                if tut_player.grid_x == 13 and tut_player.grid_y == 4:
                    tut_state = 5
                    tut_sub_step = 0
                    tut_current_text = tut_dialogues[tut_state][tut_sub_step]
                    tut_char_idx = 0.0

        elif game_state == "PLAYING" and not game_over:
            if not heli_coin.active and not player.is_heli:
                heli_spawn_timer -= dt
                if heli_spawn_timer <= 0:
                    heli_coin.spawn(player, obstacles)
            
            if heli_coin.active and not player.is_moving and player.grid_x == heli_coin.grid_x and player.grid_y == heli_coin.grid_y:
                play_item_heli_sound()  # ✅ 아이템 획득 1회
                player.is_heli = True
                player.image = player.heli_images[player.direction]
                heli_coin.hide()
                start_heli_loop()       # ✅ 헬기 루프 시작
                game_msg = "헬기로 변신!! 지형과 장애물을 무시하고 비행하세요!"

            if dx != 0 or dy != 0:
                player.move(dx, dy, obstacles, current_map=MAP_DATA)
            player.update()

            if fail_banner_timer > 0:
                fail_banner_timer -= dt
            if animal_pop > 0:
                animal_pop -= dt
            if complete_timer > 0:
                complete_timer -= dt
                if complete_timer <= 0:
                    hud_state = "PATIENT_WAIT"
            if prank_call_timer > 0:
                prank_call_timer -= dt
            stage_time -= dt
            if stage_time <= 0 and not game_over:
                stage_time = 0
                game_over = True
                game_msg = "TIME OVER!"
                stop_bgm()
                play_game_over_sound()
                    # ✅ [추가] 스테이지 종료 시 헬기 루프 무조건 종료
                stop_heli_loop()
                if player.is_heli:
                    player.is_heli = False
                    player.image = player.car_images[player.direction]

                if player.has_patient or (current_patient and (not current_patient.is_fake)):
                    failed_patients += 1
                    failed_animals.append(ANIMAL_NAMES[animal_cycle_idx])

                # ✅ Stage1/Stage2 공통: RESULT 들어가기 전에 무조건 무음
                stop_bgm()

                result = show_stage_result_screen(
                    screen=screen,
                    clock=clock,
                    bg_image_path=(result_stage1_bg_path if stage == 1 else result_bg_path),
                    stage=stage,
                    saved_count=saved_patients,
                    failed_count=failed_patients,
                    saved_animal_names=saved_animals,
                    failed_animal_names=failed_animals
                )
                
                
                if result == "QUIT":
                        running = False
                else:
                    if stage == 1:
                        stop_bgm()
                        
                        show_stage2_popup(screen, clock)
                        
                        stage = 2
                    
                        active_hospitals = pick_active_hospitals(stage)

                        stage_time = 60.0
                        golden_time = 15.0
                        time_limit_played = False

                        saved_patients = 0
                        failed_patients = 0
                        saved_animals = []
                        failed_animals = []
                        animal_cycle_idx = 0   
                        animal_idx = 0
                        animal_pop = 0.0

                        game_over = False
                        hud_state = "PATIENT_WAIT"
                        fail_banner_timer = 0.0
                        complete_timer = 0.0
                        player.has_patient = False

                        # ==========================================
                        # [추가 및 수정된 부분] 구급차/헬기 및 위치 초기화
                        # ==========================================
                        # 1. 맵에 생성된 헬기 코인 숨기고 타이머 초기화
                        heli_coin.hide()
                        heli_spawn_timer = random.uniform(15.0, 20.0)

                        # 2. 플레이어가 헬기 상태라면 구급차로 되돌리기
                        if player.is_heli:
                            stop_heli_loop()
                            player.is_heli = False
                            
                        # 3. 구급차 위치 및 방향 초기화 (시작 위치인 6, 6으로)
                        player.direction = "right"
                        player.image = player.car_images[player.direction]
                        player.grid_x, player.grid_y = 6, 6
                        player.pixel_x, player.pixel_y = 6 * TILE_SIZE, 6 * TILE_SIZE
                        player.target_x, player.target_y = player.pixel_x, player.pixel_y
                        player.rect.topleft = (player.pixel_x, player.pixel_y)
                        player.is_moving = False
                        # ==========================================

                        if current_patient:
                            current_patient.kill()
                        current_patient, new_active = respawn_patient_and_shuffle_hospitals(stage, all_sprites)
                        if new_active is not None:
                            active_hospitals = new_active

                        for obs in obstacles:
                            obs.kill()
                        obstacles = generate_safe_obstacles(5, player, current_patient)
                        all_sprites.add(obstacles)

                        game_msg = "STAGE 2 시작! 병원 2곳만 활성화되었습니다!"
                        play_bgm("game_ing")
                    else:
                        stop_bgm() # 재생 중인 배경음악 끄기
                        stop_heli_loop()
                        show_outro_video(screen, clock) # 엔딩 영상 재생!
                        show_ending_credit(screen, clock) # 1. 크레딧 풀스크린 재생
                        
                        choice = show_restart_popup(screen, clock) # 2. 재시작 여부 묻기
                        if choice == "RESTART":
                            return True  # True를 반환하면 게임이 처음부터 재시작됩니다!
                        else:
                            return False # False를 반환하면 게임이 완전 종료됩니다.

            if hud_state in ("PATIENT_WAIT", "RESCUING"):
                golden_time -= dt
                if (not time_limit_played) and (golden_time <= 2.0) and (golden_time > 0.0):
                    play_time_limit_sound()
                    time_limit_played = True

                if golden_time <= 0:
                    golden_time = 0
                    hud_state = "WAIT"
                    fail_banner_timer = 1.5
                    time_limit_played = False

                    if player.has_patient:
                        game_msg = "골든타임 초과! 이송 실패.."
                    else:
                        game_msg = "골든타임 초과! 환자 상태 악화.."

                    failed_patients += 1
                    failed_animals.append(ANIMAL_NAMES[animal_cycle_idx])
                    animal_cycle_idx = (animal_cycle_idx + 1) % len(ANIMAL_NAMES)

                    player.has_patient = False

                    if player.is_heli:
                        stop_heli_loop()
                        player.is_heli = False
                        player.image = player.car_images[player.direction]
                        heli_spawn_timer = random.uniform(20.0, 30.0)

                    current_patient = Patient()                   
                    all_sprites.add(current_patient)

                    for obs in obstacles:
                        obs.kill()
                    obstacles = generate_safe_obstacles(5, player, current_patient)
                    all_sprites.add(obstacles)

                    animal_idx = (animal_idx + 1) % 8
                    animal_pop = 0.35

                    golden_time = 15.0
                    time_limit_played = False
                    hud_state = "PATIENT_WAIT"
        
        # ===============================
        # [화면 그리기]
        # ===============================
        if game_state == "TUTORIAL":
            # 1. 튜토리얼 맵 배경 전체 렌더링
            game_surface.blit(tut_bg_image, (0, 0))

            # 2. 목적지 병원 렌더링 (가장 우측 도로 끝)
            game_surface.blit(hospital_active_surf, (13 * TILE_SIZE, 4 * TILE_SIZE))

            # 3. 파란 집 항상 렌더링 (환자 발생 위치 5, 5)
            house_x, house_y = 5, 5
            game_surface.blit(tut_house_off, (house_x * TILE_SIZE, house_y * TILE_SIZE))

            # 4. 환자 미탑승 시 깜빡이는 효과 (파란 집 위에 겹치기)
            blink = (pygame.time.get_ticks() // 500) % 2 == 0
            if not tut_player.has_patient and blink:
                game_surface.blit(tut_on_house, (house_x * TILE_SIZE, house_y * TILE_SIZE))

            # 5. 플레이어 및 스프라이트 그리기
            tut_sprites.draw(game_surface)
            game_surface.blit(tut_player.image, tut_player.rect) 
            
            # 6. 대화창 (하단 흰색 영역에 배치)
            dialog_rect = pygame.Rect(0, 7 * TILE_SIZE, GAME_WIDTH, 3 * TILE_SIZE)
            pygame.draw.rect(game_surface, (40, 50, 65), dialog_rect)
            pygame.draw.rect(game_surface, WHITE, dialog_rect, 4)
            
            lines = tut_typed_text.split('\n')
            start_y = 7 * TILE_SIZE + 40
            for i, line in enumerate(lines):
                draw_text(game_surface, line, dialog_font, WHITE, 50, start_y + i * 45)
            lines = tut_typed_text.split('\n')
            start_y = 7 * TILE_SIZE + 40
            for i, line in enumerate(lines):
                draw_text(game_surface, line, dialog_font, WHITE, 50, start_y + i * 45)

            # ==========================================
            # 👇 여기서부터 깜빡이는 안내 문구 추가!
            # ==========================================
            # 타이핑이 끝났을 때만 안내 문구 표시
            if tut_char_idx >= len(tut_current_text):
                if (pygame.time.get_ticks() // 500) % 2 == 0:
                    prompt_font = get_custom_font(24)
                    prompt_x = GAME_WIDTH - 40
                    prompt_y = GAME_HEIGHT - 30 
                    
                    # 1. 단순히 다음 설명으로 넘어가는 단계일 때 (SPACE)
                    if (tut_state == 0 and tut_sub_step == 0) or \
                       (tut_state == 1 and tut_sub_step == 0) or \
                       (tut_state == 3 and tut_sub_step == 0):
                        draw_text(game_surface, "▶ [SPACE] 다음", prompt_font, YELLOW, prompt_x, prompt_y, align="bottomright")
                    
                    # 2. 마지막 단계에서 실전 투입을 대기할 때 (ENTER)
                    elif tut_state == 6:
                        draw_text(game_surface, "▶ [ENTER] 출동!", prompt_font, RED, prompt_x, prompt_y, align="bottomright")
            # ==========================================

        elif game_state == "PLAYING":
            game_surface.fill(WHITE)  
            for y in range(len(MAP_DATA)):
                for x in range(len(MAP_DATA[0])):
                    img_idx = y * len(MAP_DATA[0]) + x
                    game_surface.blit(map_images[img_idx], (x * TILE_SIZE, y * TILE_SIZE))
            
            for (hx, hy) in HOSPITAL_COORDS:
                if (hx, hy) in active_hospitals:
                    game_surface.blit(hospital_active_surf, (hx * TILE_SIZE, hy * TILE_SIZE))
                else:
                    game_surface.blit(hospital_inactive_surf, (hx * TILE_SIZE, hy * TILE_SIZE))

            blink = (pygame.time.get_ticks() // 500) % 2 == 0

            for (hx, hy), on_img in on_house_surfaces.items():
                if not player.has_patient and current_patient.grid_x == hx and current_patient.grid_y == hy and blink:
                    game_surface.blit(on_img, (hx * TILE_SIZE, hy * TILE_SIZE))

            all_sprites.draw(game_surface)
            game_surface.blit(player.image, player.rect) 
            msg_bg = pygame.Surface((game_surface.get_width(), 50))
            msg_bg.set_alpha(150)
            msg_bg.fill(BLACK)
            game_surface.blit(msg_bg, (0, 0))
            msg_surf = font.render(game_msg, True, WHITE)
            game_surface.blit(msg_surf, (20, 10))

            if prank_call_timer > 0:
                prank_font = get_custom_font(60, bold=True)
                
                # 반투명 검은색 배경 배너
                banner_rect = pygame.Rect(0, GAME_HEIGHT // 2 - 50, GAME_WIDTH, 100)
                banner_surf = pygame.Surface((GAME_WIDTH, 100), pygame.SRCALPHA)
                banner_surf.fill((0, 0, 0, 200)) # 약간 진한 반투명
                game_surface.blit(banner_surf, banner_rect.topleft)
                
                # 경고 문구 (깜빡이는 효과 추가)
                if (pygame.time.get_ticks() // 150) % 2 == 0:
                    draw_text(game_surface, "🚨 장난전화 발생! 환자 재배치! 🚨", prank_font, RED, GAME_WIDTH // 2, GAME_HEIGHT // 2, "center")
                else:
                    draw_text(game_surface, "🚨 장난전화 발생! 환자 재배치! 🚨", prank_font, YELLOW, GAME_WIDTH // 2, GAME_HEIGHT // 2, "center")

        status_text = "구조 대기 중 (SPACE로 탑승)"
        if game_state == "TUTORIAL":
            status_text = "튜토리얼 훈련 중"
        elif hud_state == "RESCUING":
            status_text = "구조 중! (병원에서 SPACE)"
        elif hud_state == "COMPLETE":
            status_text = "구조 완료"

        hud.update(
            dt=dt,
            stage="TUTORIAL" if game_state == "TUTORIAL" else stage,
            
            stage_time_left=stage_time,
            golden_time_left=golden_time,
            saved_count=saved_patients,
            golden_running=(hud_state in ("PATIENT_WAIT", "RESCUING")),
            fail_banner_left=fail_banner_timer,
            status_text=status_text,
            stage_running=(not game_over and game_state == "PLAYING"),
            is_complete=(hud_state == "COMPLETE"),
            animal_index=animal_idx,
            animal_pop_t=animal_pop
        )
        hud.draw(hud_surface)

        screen.fill(BLACK)
        screen.blit(game_surface, (0, 0))
        screen.blit(hud_surface, (GAME_WIDTH, 0))

        pygame.display.flip()

    return False


if __name__ == "__main__":
    while True:
        # 게임이 완전 종료(False)를 반환하면 while문을 빠져나감
        if not main():
            break
            
    # 여기서 최종적으로 한 번만 pygame 종료 처리
    pygame.quit()
    sys.exit()