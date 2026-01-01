
"""
BART in PsychoPy
- Single-page intro, practice (3), main (60)
- Block summaries after 20/40 and final 60
- Left-side balloon, dark-grey HUD cards on right
- Bottom prompts with dark-grey boxes
- Deterministic explosion threshold per trial
- CSV outputs: subjects.csv, trials.csv, blocks.csv
"""

import os
import csv
import random
import math
from psychopy import core, data, event, gui, sound, visual

# Appearance
BG_COLOR     = [0.85, 0.85, 0.85]  # window background
CARD_FILL    = [0.20, 0.20, 0.20]  # dark-grey cards/panels
CARD_OPACITY = 0.96

# Text color policy
COLOR_ON_CARD  = 'white'  # use on dark boxes/panels
COLOR_ON_PLAIN = 'black'  # use directly on the light background

# Fonts
FONT_MAIN = 'Arial'
FONT_MONO = 'Menlo'

# Window and geometry
WIN_WIDTH  = 1280
WIN_HEIGHT = 720
BALLOON_POS_PIX = (-260, 40)      # left column center
PANEL_WIDTH_PIX  = 680
PANEL_HEIGHT_PIX = 560
MAX_RADIUS = (min(PANEL_WIDTH_PIX, PANEL_HEIGHT_PIX) // 2) - 6  # clamp inside panel

# Balloon growth
START_RADIUS = 10          # small start (diameter 20 px)
MIN_RADIUS   = START_RADIUS
GROWTH_PCT   = 0.025       # per pump; at least +1 px enforced below

# Task configuration
COLOR_LIST  = ['red', 'green', 'blue']
MAX_PUMPS   = [8, 32, 12]  # three risk types
REPETITIONS = 20           # 3 colors × 20 = 60 trials
REWARD      = 0.5
CURRENCY    = '€'

# Keys
KEY_PUMP = 'space'
KEY_NEXT = 'return'
KEY_QUIT = 'escape'
KEY_CONT = 'space'

# Messages
ABSENT_MESSAGE = "You've waited too long! The balloon deflated. Your temporary earnings are lost."
FINAL_MESSAGE  = "Well done! You banked a total of {:.2f} €. Thank you for your participation."

# Animation settings
CASHOUT_ANIM_DURATION = 0.0

# Randomization for counterfactual potential
CF_MASTER_SEED = 910273

# Outputs
TRIALS_CSV   = "trials.csv"
SUBJECTS_CSV = "subjects.csv"
BLOCKS_CSV   = "blocks.csv"


# ---------- Utilities ----------

def fmt_eur(v):
    try:
        return f"{float(v):.2f} {CURRENCY}"
    except Exception:
        return f"{v} {CURRENCY}"

def csv_append(path, header, row):
    """Append a row to CSV, writing header if file does not exist."""
    write_header = not os.path.exists(path)
    with open(path, 'a', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        if write_header:
            w.writerow(header)
        w.writerow(row)


# ---------- Window ----------

win = visual.Window(
    size=(WIN_WIDTH, WIN_HEIGHT),
    units='pix',
    colorSpace='rgb',
    color=BG_COLOR,
    fullscr=False,
    allowGUI=True,
    waitBlanking=True
)


# ---------- Optional assets ----------

def safe_image(image_path, size, pos):
    """Load an image if present; otherwise return None."""
    try:
        if os.path.exists(image_path):
            return visual.ImageStim(win, image=image_path, size=size, units='pix',
                                    interpolate=True, pos=pos)
    except Exception:
        return None
    return None

# Collect/Bank sound (replaces slot_machine)
try:
    collect_sound = sound.Sound('collect_sound.ogg')
except Exception:
    collect_sound = None

# Pop sound
try:
    pop_sound    = sound.Sound('pop.ogg')
except Exception:
    pop_sound = None


# ---------- Right-side HUD cards ----------

RIGHT_X    = 0.62
BOX_Y_TOP  = 0.38
BOX_Y_MID  = -0.02
BOX_Y_BOT  = -0.42
card_w, card_h = 0.58, 0.20

def card(x, y):
    return visual.Rect(win, width=card_w, height=card_h, units='norm',
                       pos=(x, y), fillColor=CARD_FILL, lineColor=None, opacity=CARD_OPACITY)

card_top = card(RIGHT_X, BOX_Y_TOP)
card_mid = card(RIGHT_X, BOX_Y_MID)
card_bot = card(RIGHT_X, BOX_Y_BOT)

LABEL_H = 0.055
VALUE_H = 0.085

label_top = visual.TextStim(win, color=COLOR_ON_CARD, font=FONT_MAIN, height=LABEL_H,
                            units='norm', pos=(RIGHT_X, BOX_Y_TOP+0.055),
                            text='Possible money for this balloon', alignText='center')
label_mid = visual.TextStim(win, color=COLOR_ON_CARD, font=FONT_MAIN, height=LABEL_H,
                            units='norm', pos=(RIGHT_X, BOX_Y_MID+0.055),
                            text='Collected money so far', alignText='center')
label_bot = visual.TextStim(win, color=COLOR_ON_CARD, font=FONT_MAIN, height=LABEL_H,
                            units='norm', pos=(RIGHT_X, BOX_Y_BOT+0.055),
                            text='Balloon count', alignText='center')

val_top = visual.TextStim(win, color=COLOR_ON_CARD, font=FONT_MONO, height=VALUE_H,
                          units='norm', pos=(RIGHT_X, BOX_Y_TOP-0.035),
                          text='0.00 €', alignText='center')
val_mid = visual.TextStim(win, color=COLOR_ON_CARD, font=FONT_MONO, height=VALUE_H,
                          units='norm', pos=(RIGHT_X, BOX_Y_MID-0.035),
                          text='0.00 €', alignText='center')
val_bot = visual.TextStim(win, color=COLOR_ON_CARD, font=FONT_MONO, height=VALUE_H,
                          units='norm', pos=(RIGHT_X, BOX_Y_BOT-0.035),
                          text='0 / 60', alignText='center')


# ---------- Bottom prompts with boxes ----------

PROMPT_POS_LEFT  = (-260, -300)
PROMPT_POS_RIGHT = ( 260, -300)
PROMPT_BG_SIZE   = (420, 64)

prompt_bg_left  = visual.Rect(win, width=PROMPT_BG_SIZE[0], height=PROMPT_BG_SIZE[1],
                              units='pix', pos=PROMPT_POS_LEFT,
                              fillColor=CARD_FILL, opacity=CARD_OPACITY, lineColor=None)
prompt_bg_right = visual.Rect(win, width=PROMPT_BG_SIZE[0], height=PROMPT_BG_SIZE[1],
                              units='pix', pos=PROMPT_POS_RIGHT,
                              fillColor=CARD_FILL, opacity=CARD_OPACITY, lineColor=None)

prompt_left  = visual.TextStim(win, color=COLOR_ON_CARD, font=FONT_MAIN, height=24,
                               units='pix', pos=PROMPT_POS_LEFT,
                               text='Press RETURN to bank', alignText='center')
prompt_right = visual.TextStim(win, color=COLOR_ON_CARD, font=FONT_MAIN, height=24,
                               units='pix', pos=PROMPT_POS_RIGHT,
                               text='Press SPACE to pump', alignText='center')

center_msg = visual.TextStim(win, color=COLOR_ON_PLAIN, font=FONT_MAIN, height=32,
                             units='pix', pos=(0, 0), alignText='center',
                             wrapWidth=1000, text='')


# ---------- Balloon stimulus ----------

balloon_circle = visual.Circle(
    win,
    radius=START_RADIUS,
    units='pix',
    pos=BALLOON_POS_PIX,
    fillColor=COLOR_LIST[0],
    lineColor=None,
    lineWidth=0,
    edges=128
)

def set_balloon(circle_color, radius):
    """Set balloon color/size, clamped inside left panel."""
    r = int(max(MIN_RADIUS, min(MAX_RADIUS, radius)))
    balloon_circle.fillColor  = circle_color
    balloon_circle.radius     = r
    balloon_circle.pos        = BALLOON_POS_PIX
    balloon_circle.draw()
    return r


# ---------- Pop animation ----------

def play_pop_once(pos_pix, radius):
    frame_size = (2*radius, 2*radius)
    pop1 = safe_image('pop1.png', size=frame_size, pos=pos_pix)
    pop2 = safe_image('pop2.png', size=frame_size, pos=pos_pix)
    if pop_sound:
        try: pop_sound.play()
        except Exception: pass
    if pop1 and pop2:
        pop1.draw(); win.flip(); core.wait(0.25)
        pop2.draw(); win.flip(); core.wait(0.25)
        return
    # Fallback: ring then burst
    ring1 = visual.Circle(win, radius=radius, units='pix', pos=pos_pix,
                          fillColor=None, lineColor='white', lineWidth=6, edges=64)
    ring1.draw(); win.flip(); core.wait(0.25)
    verts = []
    outer = radius
    inner = max(6, int(radius * 0.55))
    for i in range(24):
        angle = (i/24.0) * 2*math.pi
        r = outer if i % 2 == 0 else inner
        verts.append((pos_pix[0] + r*math.cos(angle), pos_pix[1] + r*math.sin(angle)))
    burst = visual.ShapeStim(win, vertices=verts, units='pix',
                             fillColor='white', lineColor='white', closeShape=True)
    burst.draw(); win.flip(); core.wait(0.25)


# ---------- Intro page (centered, plain background) ----------

def show_intro_single_page():
    win.colorSpace = 'rgb'
    win.color      = BG_COLOR
    title = visual.TextStim(
        win, text="Balloon Task — Instructions",
        units='pix', pos=(0, 160),
        color=COLOR_ON_PLAIN, font=FONT_MAIN, height=40,
        alignText='center', wrapWidth=1000
    )
    body = visual.TextStim(
        win,
        text=(
            "Inflate the balloon to earn money.\n\n"
            "Press SPACE to pump and add €. Press RETURN to bank your amount.\n\n"
            "If the balloon pops, you lose the unbanked money.\n\n"
            "Aim to bank as much as you can."
        ),
        units='pix', pos=(0, -10),
        color=COLOR_ON_PLAIN, font=FONT_MAIN, height=26,
        alignText='center', wrapWidth=1000
    )
    footer = visual.TextStim(
        win, text="Press SPACE to start practice",
        units='pix', pos=(0, -280),
        color=COLOR_ON_PLAIN, font=FONT_MAIN, height=24,
        alignText='center'
    )
    title.draw(); body.draw(); footer.draw()
    win.flip()
    event.clearEvents(eventType='keyboard')
    while True:
        keys = event.getKeys()
        if KEY_QUIT in keys:
            return False
        if KEY_CONT in keys or KEY_NEXT in keys:
            return True
        core.wait(0.01)


# ---------- Trial HUD drawing ----------

def draw_hud_by_radius(radius_px, color_name, tempBank, permBank, count_text):
    """One frame: balloon, right cards, bottom prompts."""
    win.colorSpace = 'rgb'
    win.color      = BG_COLOR
    set_balloon(color_name, radius_px)

    # Right cards and their labels/values (white on dark)
    card_top.draw(); card_mid.draw(); card_bot.draw()
    label_top.draw(); label_mid.draw(); label_bot.draw()
    val_top.text = fmt_eur(tempBank)
    val_mid.text = fmt_eur(permBank)
    val_bot.text = count_text
    val_top.draw(); val_mid.draw(); val_bot.draw()

    # Bottom prompt boxes (white text on dark)
    prompt_bg_left.draw(); prompt_bg_right.draw()
    prompt_left.draw(); prompt_right.draw()

    win.flip()

def animate_total_by_radius(oldTotal, newTotal, radius_px, color_name, tempBank, permBank, count_text, duration=CASHOUT_ANIM_DURATION):
    """Animate banking total if duration > 0."""
    if duration <= 0.0 or abs(newTotal - oldTotal) < 0.005:
        draw_hud_by_radius(radius_px, color_name, tempBank, newTotal, count_text)
        return
    clock = core.Clock()
    while True:
        t = min(clock.getTime()/duration, 1.0)
        disp = oldTotal + t*(newTotal - oldTotal)
        draw_hud_by_radius(radius_px, color_name, tempBank, disp, count_text)
        if t >= 1.0: break


# ---------- Explosion threshold per trial (deterministic) ----------

def sample_explosion_threshold(max_pumps, subject_id, trial_idx):
    """Return pump number at which explosion would occur (1..max_pumps)."""
    rng = random.Random(CF_MASTER_SEED + (hash(f"{subject_id}-{trial_idx}") & 0xffffffff))
    return rng.randint(1, max_pumps)


# ---------- Summary layout ----------

ROW_START_Y =  0.50
ROW_STEP_Y  = -0.17
ROW_X_LABEL = -0.35
ROW_X_VALUE =  0.30
LABEL_ROW_H = 0.068
VALUE_ROW_H = 0.074

def show_summary(title_suffix, stats, participant_id=None, scope=None):
    """Summary panel with labels on left and values right-aligned."""
    win.colorSpace = 'rgb'
    win.color      = BG_COLOR

    missed    = max(0.0, stats['potential'] - stats['earned'])
    avg_pumps = (stats['total_pumps_unexploded']/stats['unexploded']) if stats['unexploded']>0 else 0.0

    # Panel background
    panel = visual.Rect(win, width=1.70, height=1.20, units='norm',
                        pos=(0, 0), fillColor=CARD_FILL, lineColor=None, opacity=CARD_OPACITY)
    panel.draw()

    title = visual.TextStim(win, color=COLOR_ON_CARD, font=FONT_MAIN, height=0.095,
                            units='norm', pos=(0, 0.72),
                            text=f"Summary — {title_suffix}", alignText='center')
    title.draw()

    labels = [
        "Total money you could have earned",
        "Total money earned",
        "Missed potential money",
        "Total number balloons",
        "Total number unexploded balloons",
        "Total number exploded balloons",
        "Average number of pump ups per unexploded balloon"
    ]
    values = [
        fmt_eur(stats['potential']),
        fmt_eur(stats['earned']),
        fmt_eur(missed),
        f"{stats['total_balloons']}",
        f"{stats['unexploded']}",
        f"{stats['exploded']}",
        f"{avg_pumps:.2f}"
    ]

    y = ROW_START_Y
    for lab, val in zip(labels, values):
        t_lab = visual.TextStim(
            win, color=COLOR_ON_CARD, font=FONT_MAIN, height=LABEL_ROW_H,
            units='norm', pos=(ROW_X_LABEL, y), text=lab,
            alignText='left', wrapWidth=0.90
        )
        t_val = visual.TextStim(
            win, color=COLOR_ON_CARD, font=FONT_MONO, height=VALUE_ROW_H,
            units='norm', pos=(ROW_X_VALUE, y), text=val,
            alignText='right'
        )
        t_lab.draw(); t_val.draw()
        y += ROW_STEP_Y

    cont = visual.TextStim(win, color=COLOR_ON_CARD, font=FONT_MAIN, height=0.080,
                           units='norm', pos=(0, -0.78), text='Press SPACE to continue',
                           alignText='center')
    cont.draw()
    win.flip()

    # Save a row for the block in blocks.csv
    if participant_id and scope:
        csv_append(
            BLOCKS_CSV,
            header=[
                'participant_id','scope','total_balloons','unexploded','exploded',
                'total_pumps_unexploded','earned','potential','missed'
            ],
            row=[
                participant_id,
                scope,
                stats['total_balloons'],
                stats['unexploded'],
                stats['exploded'],
                stats['total_pumps_unexploded'],
                f"{stats['earned']:.2f}",
                f"{stats['potential']:.2f}",
                f"{max(0.0, stats['potential'] - stats['earned']):.2f}"
            ]
        )

    event.clearEvents(eventType='keyboard')
    while True:
        keys = event.getKeys()
        if KEY_QUIT in keys: break
        if KEY_CONT in keys or KEY_NEXT in keys: break
        core.wait(0.01)


# ---------- Trial creation ----------

def create_trials(colors, maxPumps, reps, reward):
    """Return TrialHandler with full randomization over color × reps."""
    trialList = [{'color': colors[i], 'maxPumps': maxPumps[i], 'reward': reward}
                 for i in range(len(colors))]
    random.seed(52472)
    return data.TrialHandler(trialList, nReps=reps, method='fullRandom')

def create_practice_trials():
    """Three practice trials in a fixed order."""
    trialList = [{'color': COLOR_LIST[i], 'maxPumps': MAX_PUMPS[i], 'reward': REWARD}
                 for i in range(len(COLOR_LIST))]
    return data.TrialHandler(trialList, nReps=1, method='sequential')


# ---------- Practice ----------

def run_practice(trials):
    permBank = 0.0
    for idx, trial in enumerate(trials, start=1):
        tempBank = 0.0
        nPumps   = 0
        pop      = False
        continuePumping = True
        current_radius = START_RADIUS

        while continuePumping and not pop:
            draw_hud_by_radius(current_radius, trial['color'], tempBank, permBank, f"Practice {idx}/3")
            event.clearEvents(eventType='keyboard')
            key = event.waitKeys(keyList=[KEY_PUMP, KEY_NEXT, KEY_QUIT], maxWait=15)

            if not key:
                center_msg.text = ABSENT_MESSAGE
                center_msg.color = COLOR_ON_PLAIN
                center_msg.draw(); win.flip(); core.wait(4)
                continuePumping = False

            elif key[0] == KEY_QUIT:
                return permBank

            elif key[0] == KEY_NEXT:
                # play collect sound on banking
                if collect_sound:
                    try: collect_sound.play()
                    except Exception: pass
                permBank += tempBank
                tempBank = 0.0
                continuePumping = False

            elif key[0] == KEY_PUMP:
                # Inflate first (enforce at least +1 px)
                next_radius = max(current_radius + 1,
                                  int(round(current_radius * (1.0 + GROWTH_PCT))))
                current_radius = min(MAX_RADIUS, next_radius)
                nPumps += 1

                draw_hud_by_radius(current_radius, trial['color'], tempBank, permBank, f"Practice {idx}/3")

                # Practice pop logic: simple increasing hazard
                if nPumps >= trial['maxPumps']:
                    play_pop_once(BALLOON_POS_PIX, current_radius)
                    tempBank = 0.0; pop = True
                else:
                    burst_p = 1.0 / (trial['maxPumps'] - nPumps)
                    if random.random() < burst_p:
                        play_pop_once(BALLOON_POS_PIX, current_radius)
                        tempBank = 0.0; pop = True
                    else:
                        tempBank += REWARD
    return permBank


# ---------- Main experiment ----------

def bart():
    # Participant info
    infoDlg = gui.DlgFromDict(
        title='BART',
        dictionary={'id':'0','age':'0','gender':['female','male','other'],
                    'date':data.getDateStr(format="%Y-%m-%d_%H:%M"),'version':23.0},
        fixed=['version'],
        order=['id','age','gender','date','version']
    )
    if not infoDlg.OK:
        win.close(); core.quit(); return
    info = infoDlg.dictionary
    subject_id = str(info.get('id', '0'))

    # Save subject row
    csv_append(
        SUBJECTS_CSV,
        header=['participant_id','age','gender','date'],
        row=[subject_id, info['age'], info['gender'], info['date']]
    )

    # Intro
    if not show_intro_single_page():
        win.close(); core.quit(); return

    # Practice
    _ = run_practice(create_practice_trials())

    # Pre-main prompt on plain background
    pre_main = visual.TextStim(
        win, color=COLOR_ON_PLAIN, font=FONT_MAIN, height=30, units='pix', pos=(0, 30),
        alignText='center',
        text=("The real task starts now.\n\n"
              "There are 60 balloons.\n\n"
              "Try to win as much game money as you can.")
    )
    footer = visual.TextStim(win, color=COLOR_ON_PLAIN, font=FONT_MAIN, height=24, units='pix',
                             pos=(0, -300), alignText='center',
                             text="Press SPACE to begin")
    pre_main.draw(); footer.draw(); win.flip()
    event.clearEvents(eventType='keyboard')
    while True:
        keys = event.getKeys()
        if KEY_QUIT in keys: win.close(); core.quit(); return
        if KEY_CONT in keys: break
        core.wait(0.01)

    # Trial list for main (60)
    trials = create_trials(COLOR_LIST, MAX_PUMPS, REPETITIONS, REWARD)

    overall = {'total_balloons':0,'unexploded':0,'exploded':0,
               'total_pumps_unexploded':0,'earned':0.0,'potential':0.0}
    block   = {'total_balloons':0,'unexploded':0,'exploded':0,
               'total_pumps_unexploded':0,'earned':0.0,'potential':0.0}

    permBank = 0.0

    trial_header = [
        'participant_id','trial_number','color','max_pumps','pumps_made',
        'exploded','earned_this','banked_total_after','potential_this','missed_this','timestamp'
    ]

    for idx, trial in enumerate(trials, start=1):
        tempBank = 0.0
        nPumps   = 0
        pop      = False
        continuePumping = True
        earned_this = 0.0
        potential_this = 0.0
        current_radius = START_RADIUS

        # Explosion threshold for this trial
        E = sample_explosion_threshold(trial['maxPumps'], subject_id, idx)
        last_safe = E - 1

        while continuePumping and not pop:
            draw_hud_by_radius(current_radius, trial['color'], tempBank, permBank, f"{idx} / 60")
            event.clearEvents(eventType='keyboard')
            key = event.waitKeys(keyList=[KEY_PUMP, KEY_NEXT, KEY_QUIT], maxWait=15)

            if not key:
                center_msg.text = ABSENT_MESSAGE
                center_msg.color = COLOR_ON_PLAIN
                center_msg.draw(); win.flip(); core.wait(4)
                continuePumping = False
                earned_this = 0.0
                potential_this = 0.0

            elif key[0] == KEY_QUIT:
                win.close(); core.quit(); return

            elif key[0] == KEY_NEXT:
                # Bank current temp amount (play collect sound)
                earned_this = tempBank
                newTotal    = permBank + earned_this
                if collect_sound:
                    try: collect_sound.play()
                    except Exception: pass
                animate_total_by_radius(permBank, newTotal, current_radius, trial['color'], tempBank, permBank, f"{idx} / 60",
                                        duration=CASHOUT_ANIM_DURATION)
                permBank    = newTotal
                tempBank    = 0.0
                continuePumping = False

                # Counterfactual potential (last safe pump if kept pumping)
                potential_this = last_safe * REWARD

                # Update totals
                block['total_balloons'] += 1
                block['unexploded']     += 1
                block['total_pumps_unexploded'] += nPumps
                block['earned']         += earned_this
                block['potential']      += potential_this

                overall['total_balloons'] += 1
                overall['unexploded']     += 1
                overall['total_pumps_unexploded'] += nPumps
                overall['earned']         += earned_this
                overall['potential']      += potential_this

            elif key[0] == KEY_PUMP:
                # Inflate first, ensure visible change
                next_radius = max(current_radius + 1,
                                  int(round(current_radius * (1.0 + GROWTH_PCT))))
                current_radius = min(MAX_RADIUS, next_radius)
                nPumps += 1

                draw_hud_by_radius(current_radius, trial['color'], tempBank, permBank, f"{idx} / 60")

                # Explosion check against deterministic threshold
                if nPumps >= E:
                    potential_this = last_safe * REWARD
                    play_pop_once(BALLOON_POS_PIX, current_radius)
                    tempBank = 0.0
                    pop      = True
                    earned_this = 0.0

                    block['total_balloons'] += 1
                    block['exploded']       += 1
                    block['potential']      += potential_this

                    overall['total_balloons'] += 1
                    overall['exploded']       += 1
                    overall['potential']      += potential_this
                else:
                    tempBank += REWARD

        # Save trial row
        missed_this = potential_this - earned_this
        csv_append(
            TRIALS_CSV,
            header=trial_header,
            row=[
                subject_id,
                idx,
                trial['color'],
                trial['maxPumps'],
                nPumps,
                int(pop),
                f"{earned_this:.2f}",
                f"{permBank:.2f}",
                f"{potential_this:.2f}",
                f"{missed_this:.2f}",
                data.getDateStr(format="%Y-%m-%d_%H:%M:%S")
            ]
        )

        # Block summaries at 20 & 40
        if overall['total_balloons'] in (20, 40):
            start = overall['total_balloons'] - 19
            end   = overall['total_balloons']
            show_summary(f"Trials {start}–{end}", block, participant_id=subject_id, scope=f"block_{start}_{end}")
            block = {'total_balloons':0,'unexploded':0,'exploded':0,
                     'total_pumps_unexploded':0,'earned':0.0,'potential':0.0}

    # Final summary and closing message
    show_summary("All 60 Trials", overall, participant_id=subject_id, scope="final_60")
    center_msg.text  = FINAL_MESSAGE.format(overall['earned'])
    center_msg.color = COLOR_ON_PLAIN
    center_msg.draw(); win.flip()

    event.clearEvents(eventType='keyboard')
    while True:
        keys = event.getKeys()
        if KEY_QUIT in keys or KEY_CONT in keys or KEY_NEXT in keys:
            break
        core.wait(0.01)

    win.close(); core.quit()


if __name__ == "__main__":
    bart()
