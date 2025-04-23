import curses
import random
import time
import requests
import threading

WORDS = []
words_lock = threading.Lock()

class Word:
    def __init__(self, word, x):
        self.word = word
        self.x = x
        self.y = 0

def fetch_words(n=100):
    try:
        res = requests.get(f"https://random-word-api.herokuapp.com/word?number={n}")
        if res.status_code == 200:
            return res.json()
    except:
        pass
    return ["fallback", "words", "python", "keyboard", "matrix", "banana"]

def background_word_fetcher(interval=10):
    global WORDS
    while True:
        new_words = fetch_words(100)
        with words_lock:
            WORDS = new_words
        time.sleep(interval)

def get_difficulty_words(words, score):
    if score <= 5:
        return [w for w in words if 3 <= len(w) <= 5]
    elif score <= 15:
        return [w for w in words if 5 <= len(w) <= 7]
    elif score <= 30:
        return [w for w in words if 7 <= len(w) <= 10]
    else:
        return [w for w in words if len(w) > 10]

def main(stdscr):
    global WORDS
    curses.curs_set(0)
    stdscr.nodelay(1)
    stdscr.timeout(100)

    # Color setup
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_BLUE, -1)
    curses.init_pair(2, curses.COLOR_YELLOW, -1)
    curses.init_pair(3, curses.COLOR_GREEN, -1)
    curses.init_pair(4, curses.COLOR_RED, -1)

    height, width = stdscr.getmaxyx()
    score = 0
    lives = 3
    input_str = ""
    words = []
    spawn_timer = 0

    # Start fetching words
    threading.Thread(target=background_word_fetcher, daemon=True).start()
    while not WORDS:
        time.sleep(0.1)

    while True:
        stdscr.clear()
        stdscr.border(0)

        # Spawn word
        if spawn_timer == 0:
            with words_lock:
                filtered_words = get_difficulty_words(WORDS, score)
                word_text = random.choice(filtered_words if filtered_words else WORDS)
            word = Word(word_text, random.randint(1, max(1, width - len(word_text) - 2)))
            words.append(word)
            spawn_timer = 10
        else:
            spawn_timer -= 1

        # Move words
        for word in words:
            word.y += 1

        # Remove and check for missed
        for word in words[:]:
            if word.y >= height - 2:
                lives -= 1
                words.remove(word)

        # Draw words
        for word in words:
            try:
                stdscr.addstr(word.y, word.x, word.word, curses.color_pair(1))
            except curses.error:
                pass

        # Display input
        stdscr.addstr(height - 1, 2, f"> {input_str}", curses.color_pair(3))
        stdscr.addstr(0, 2, f"Score: {score} | Lives: {lives}", curses.color_pair(2))

        # Input handling
        try:
            key = stdscr.getkey()
        except:
            key = None

        if key:
            if key == '\n':
                for word in words:
                    if word.word == input_str:
                        score += 1
                        words.remove(word)
                        break
                input_str = ""
            elif key in ('KEY_BACKSPACE', '\b', '\x7f'):
                input_str = input_str[:-1]
            elif len(key) == 1 and key.isprintable():
                input_str += key

        if lives <= 0:
            stdscr.addstr(height // 2, width // 2 - 5, "GAME OVER", curses.color_pair(4) | curses.A_BOLD)
            stdscr.refresh()
            time.sleep(2)
            break

        stdscr.refresh()
        time.sleep(0.1)

curses.wrapper(main)
