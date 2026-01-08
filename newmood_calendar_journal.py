import streamlit as st
import datetime
import calendar
import random
import json
import os
import pandas as pd
import time
# --- Mood Sprout Game Imports ---
from PIL import Image
import base64 
import io
# --- Plotly Import (Needed for Insights) ---
import plotly.express as px

# -------------------- 0. Mood Sprout Helper Functions (for Pet Game)
# --------------------
 
@st.cache_data
def get_base64_image(image_path, cache_identifier=None): 
    """Converts image to Base64 for CSS background, uses cache_identifier to force reload."""
    try:
        full_path = image_path 
        with open(full_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return None
 
@st.cache_data
def load_pet_image(image_path):
    """Loads pet images using PIL (for robustness)."""
    try:
        if not os.path.exists(image_path):
            return None
        return Image.open(image_path)
    except Exception:
        return None
 
# -------------------- 1. GLOBAL CONSTANTS AND MAPPINGS (JOURNAL APP)
# --------------------
 
POINTS_PER_ENTRY = 10 
MAX_DAILY_POTION_ENTRIES = 5 # Max potions granted per day
 
st.set_page_config(page_title="🌸 Personalized Mood Journal Pro", layout="centered")

# --- 背景顏色設定 ---
BACKGROUND_COLOR = "#FAF0E6" # Linen 米白色
 
# --- Global Lists (English) ---
# ************ 修改 ACTIVITY_TAGS: 加入 Other ❓ ************
ACTIVITY_TAGS = [
    "Work 💻", "Exercise 🏋️", "Socializing 👥", "Food 🍕",
    "Family ❤️", "Hobbies 🎨", "Rest 🛋️", "Study 📚", "Travel ✈️", "Nature 🏞️", "Money 💰",
    "Other ❓"
]
 
MOOD_MAPPING = {
    "Happy": "😀", "Sad": "😢", "Angry": "😡", "Calm": "😌", 
    "Excited": "🤩", "Tired": "😴", "Anxious": "😥",
}
MOOD_SCORES = {
    "😀": 5, "🤩": 4, "😌": 3, "😴": 2, "😢": 1, "😡": 1, "😥": 1
}

# --- ACHIEVEMENT CONSTANTS (NEWLY ADDED) ---
ACHIEVEMENTS = [
    {"name": "Journaling Beginner", "desc": "Achieve 5 total entries.", "threshold": 5, "type": "total_entries"},
    {"name": "Consistent Companion", "desc": "Achieve a 7-day streak.", "threshold": 7, "type": "streak"},
    {"name": "Emotion Explorer", "desc": "Log all 7 mood types at least once.", "threshold": 7, "type": "unique_moods"},
    {"name": "Insight Master", "desc": "Log 30 total entries.", "threshold": 30, "type": "total_entries"},
]

# --- Mood Sprout Game Mappings (Updated Text and File Names) ---
SPROUT_EVOLUTION_THRESHOLD = 30 # Sprout evolution threshold
SPROUT_INITIAL_POTIONS = 5 # User request: 5 potions initially
SPROUT_IMAGE_DIR = "image" # 藥水/植物圖片資料夾
 
# Potion name to file path mapping (lowercase)
POTION_MAPPING = {
    "happy": os.path.join(SPROUT_IMAGE_DIR, "potion_happy.png"),
    "sad": os.path.join(SPROUT_IMAGE_DIR, "potion_sad.png"),
    "angry": os.path.join(SPROUT_IMAGE_DIR, "potion_angry.png"),
    "calm": os.path.join(SPROUT_IMAGE_DIR, "potion_calm.png"),
    "excited": os.path.join(SPROUT_IMAGE_DIR, "potion_excited.png"),
    "tired": os.path.join(SPROUT_IMAGE_DIR, "potion_tired.png"),
    "anxious": os.path.join(SPROUT_IMAGE_DIR, "potion_anxious.png"),
}
 
# Pet evolution image paths (Capitalized)
PET_MAPPING = {
    "Seed": os.path.join(SPROUT_IMAGE_DIR, "soil.png"), 
    "Happy": os.path.join(SPROUT_IMAGE_DIR, "plant_happy.png"), 
    "Sad": os.path.join(SPROUT_IMAGE_DIR, "plant_sad.png"), 
    "Angry": os.path.join(SPROUT_IMAGE_DIR, "plant_angry.png"), 
    "Calm": os.path.join(SPROUT_IMAGE_DIR, "plant_calm.png"), 
    "Excited": os.path.join(SPROUT_IMAGE_DIR, "plant_excited.png"), 
    "Tired": os.path.join(SPROUT_IMAGE_DIR, "plant_tired.png"), 
    "Anxious": os.path.join(SPROUT_IMAGE_DIR, "plant_anxious.png"), 
}
 
# Helper: Emoji to internal sprout name (lowercase)
EMOJI_TO_SPROUT_NAME = { 
    "😀": "happy", "😢": "sad", "😡": "angry", "😌": "calm", 
    "🤩": "excited", "😴": "tired", "😥": "anxious",
}
 
# --- Response Texts (Retained) ---
EMOTION_RESPONSES = {
    "tired": "You sound tired 😴. Rest is productive too — take time to recharge.",
    "bored": "Boredom might mean your heart craves something new 🎨. Try doing something creative today!",
    "calm": "That’s wonderful 🌿. Calmness is peace speaking softly to your soul.",
    "guilty": "Guilt shows you care 🌱. Reflect gently and forgive yourself.", 
    "anxious": "Anxiety can be heavy 😥. Breathe slowly — you’re safe and doing your best.",
    "happy": "Yay! So happy for you! 😄🎈 Let your joy shine and share your smile today!",
    "sad": f"It’s okay to feel sad 💧. Emotions flow and fade — here’s a little cheer-up joke for you:\n\n**{random.choice(['Why did the scarecrow win an award? Because he was outstanding in his field 🌾', 'I told my computer I felt sad — it gave me a byte of comfort 💻', 'Did you hear about the depressed coffee? It got mugged ☕'])}**",
    "lonely": "Loneliness is heavy 🫶. You’re not alone — I’m here listening.",
    "angry": "It’s alright to feel upset 😔. Let it out — expression is healing.",
}
 
GENERAL_RESPONSES = [
    "Thank up for sharing your entry ✍️. Remember, small steps lead to big changes.",
    "Your feelings are valid. Take a moment to focus on your breath and find peace. 🌬️",
    "It takes courage to write down your thoughts. We're here to listen to your journey! 🫂",
    "Keep up the habit of reflection! Every day is a new story waiting to unfold. 🌿",
    "Well done on making an entry today! You are prioritizing your well-being. 😊",
]
 
DAILY_PROMPTS = [
    "What is one thing that made you feel proud or accomplished today?",
    "If you could give yesterday's self one piece of advice, what would it be?",
    "Describe three sounds, smells, or sights you encountered today.",
    "Did you express gratitude to anyone today, or did someone make you feel grateful?",
    "What is one small thing you can do tomorrow to make it better?",
    "What is a new thing you learned today, no matter how small?",
]
 
SURPRISE_FACTS = [
    "Did you know a group of flamingos is called a 'flamboyance'? Stay flamboyant! 💖",
    "Fun Fact: Honey never spoils. Keep your good memories preserved like honey! 🍯",
    "Quick Riddle: What has to be broken before you can use it? A seed! Break those barriers!🌱", 
    "A moment of wonder: There are more trees on Earth than stars in the Milky Way. Keep growing! 🌳",
    "Your lucky number today is 7! May your day be seven times brighter! ✨",
]
 
FORTUNE_SLIPS = (
    # Supreme Luck (大吉 - 5 slips)
    [("Supreme Luck", "🌟", "A day of profound clarity and happiness awaits. Trust your highest vision; your energy is magnetic today.")] * 2 +
    [("Supreme Luck", "🌟", "All relationships are blessed today. Reach out and share your good fortune; it will return tenfold.")] +
    [("Supreme Luck", "🌟", "An obstacle you faced yesterday dissolves today. Unexpected success finds you when you stay open.")] +
    [("Supreme Luck", "🌟", "Inner peace is your greatest asset. Use this calm to make powerful, confident decisions.")] +
    [("Supreme Luck", "🌟", "The universe is aligning for you today. Expect a breakthrough in an area you thought was stuck.")] + 
    
    # Excellent Luck (吉 - 15 slips)
    [("Excellent Luck", "✨", "Your mind is sharp and ideas flow. Write down new goals; you have the power to achieve them.")] * 3 +
    [("Excellent Luck", "✨", "Take a risk today, especially in creative endeavors. Joy follows bold action.")] * 3 +
    [("Excellent Luck", "✨", "Unexpected kindness comes from a stranger or colleague. Pay it forward and brighten someone else's day.")] * 3 +
    [("Excellent Luck", "✨", "A lingering doubt is resolved easily. Feel lighter and move forward with purpose.")] * 3 +
    [("Excellent Luck", "✨", "The path to self-improvement is wide open. Commit to a healthy habit today.")] * 3 +

    # Good Prospect (中吉 - 15 slips)
    [("Good Prospect", "🍀", "A feeling of balance settles in. Trust the rhythm of your day and avoid unnecessary rushing.")] * 3 +
    [("Good Prospect", "🍀", "Someone needs your support. Offering a listening ear will deepen your connection.")] * 3 +
    [("Good Prospect", "🍀", "Your emotional well-being requires gentle attention. Focus on rest and simple pleasures.")] * 3 +
    [("Good Prospect", "🍀", "A small personal victory is on the horizon. Acknowledge and reward your efforts.")] * 3 +
    [("Good Prospect", "🍀", "Change is coming, but it is manageable. Prepare your mind for gentle adjustments.")] * 3 +

    # Moderate Fortune (小吉 - 10 slips)
    [("Moderate Fortune", "🌤️", "It is a day for careful planning. Avoid spontaneity and stick to your schedule for best results.")] * 2 +
    [("Moderate Fortune", "🌤️", "Energy levels are moderate. Conserve your efforts for what truly matters by saying 'no' when needed.")] * 2 +
    [("Moderate Fortune", "🌤️", "A minor misunderstanding may occur. Approach conversations with patience and seek clarity.")] * 2 +
    [("Moderate Fortune", "🌤️", "Don't dwell on perfection. Good enough is perfect for today; accept progress over flawless execution.")] * 2 +
    [("Moderate Fortune", "🌤️", "Neutral energy surrounds you. Use this quiet day for thoughtful reflection in your journal.")] * 2 +

    # Minor Challenge (凶 - 5 slips)
    [("Minor Challenge", "⚠️", "Frustration is possible. Use this as a signal to step away and seek immediate stress relief.")] +
    [("Minor Challenge", "⚠️", "A feeling of heaviness may arise. Be extra gentle with yourself and prioritize basic self-care.")] +
    [("Minor Challenge", "⚠️", "Be mindful of unnecessary spending or overcommitment. Your boundaries need protection today.")] +
    [("Minor Challenge", "⚠️", "Doubt may creep in. Remember your core strengths and seek external encouragement if needed.")] +
    [("Minor Challenge", "⚠️", "Communication requires extra effort. Write down your thoughts before speaking to avoid conflict.")]
)

# -------------------- 1.5. GLOBAL CONSTANTS AND MAPPINGS (PET GAME ADDITION)
# --------------------

# **修正：寵物圖片（pet_*.png）位於根目錄**

PET_IMAGE_PATHS = {
    "happy_dog": "pet_happy.png",    
    "sad_cat": "pet_sad.png",        
    "tired_panda": "pet_tired.png",    
    "angry_rabbit": "pet_anxious.png", 
    "calm_owl": "pet_calm.png",        
}

ANIMAL_COMPANIONS = {
    "happy_dog": {
        "name": "Happy Dog 🐶",
        "art": {"visual_path": PET_IMAGE_PATHS["happy_dog"],},
        "initial_message": "Woof! You chose 'Super Happy'! That's great! Let's play together!",
        "responses": {
            "tap": ["Woof! You booped my nose!", "Bark! Full of energy!", "Huh? What is it?"],
            "pet": ["🥰 Purrrrr... I love you!", "Feeling loved! 🐾", "Pet me more, my mood is flying high!"],
            "feed": ["Delicious! This tastes like heaven! Thank you, human!", "I love tasty treats the most! Woof!", "Full of life now! 🦴"]
        }
    },
    "sad_cat": {
        "name": "Comfort Cat 🐱",
        "art": {"visual_path": PET_IMAGE_PATHS["sad_cat"],},
        "initial_message": "Meow... You chose 'A Bit Sad'? It's okay, I'll quietly stay here with you and offer a warm rub.",
        "responses": {
            "tap": ["Don't bother me. I'm napping.", "Shhh... Be quiet, listen to my purr.", "I'm here for you."],
            "pet": ["💕 Hmph... It's comfortable, but don't think I'm clingy. Fine, just a little more...", "Grrrrrrr... (Reluctantly enjoying it)"],
            "feed": ["Oh... Is this for me? (Eats slowly) Thanks...", "Mmm, you know my taste. 🐟"]
        }
    },
    "tired_panda": {
        "name": "Chill Panda 🐼", 
        "art": {"visual_path": PET_IMAGE_PATHS["tired_panda"],},
        "initial_message": "Hoo... Hoo... Chose 'Super Tired'? Come... let's slowly... eat bamboo... together...",
        "responses": {
            "tap": ["...Mmm... A little... ticklish...", "...Slow... down...", "...What is it..."],
            "pet": ["...Wow... So... comfy... Pet... me... a little more...", "...This warm... feeling... is nice...", "...I... like... it..."],
            "feed": ["...Ah... Bamboo... is... delicious...", "...Eating... slowly... enjoying... 🌿"]
        }
    },
    "angry_rabbit": {
        "name": "Fuffy Rabbit 🐰",
        "art": {"visual_path": PET_IMAGE_PATHS["angry_rabbit"],},
        "initial_message": "You chose 'Very Angry'? I understand that puffed-up feeling! Take a deep breath, puff up like me, and slowly relax.",
        "responses": {
            "tap": ["Don't touch me! I'm still angry!", "Touch me again and I'll run away!", "💢"],
            "pet": ["(Huffs)... Fine... Just a little stroke... The anger is subsiding a bit...", "Mmm... Head rubs... That feels slightly better..."],
            "feed": ["Mine! (Guards the food) ...It's quite tasty though.", "Are you bribing me? Hmph! 🥕"]
        }
    },
    "calm_owl": {
        "name": "Peaceful Owl 🦉", 
        "art": {"visual_path": PET_IMAGE_PATHS["calm_owl"],},
        "initial_message": "Good evening~ You chose 'Calm and Relaxed'? Wonderful! Let me gaze at you peacefully, helping you unwind.",
        "responses": {
            "tap": ["Hush... I'm meditating.", "No rush, take your time.", "I'm guarding you here."],
            "pet": ["Hoo... So soft, feel my feathers.", "It's peaceful, isn't it?", "We support each other."],
            "feed": ["Thank you! A night's banquet.", "Food is good.", "Chew slowly, absorb the wisdom."]
        }
    },
}

PET_MOOD_CHOICES = {
    "Super Happy! 🥳": "happy_dog",
    "A Bit Sad 😢": "sad_cat",
    "Super Tired, Need Rest 😴": "tired_panda", 
    "Very Angry! 💢": "angry_rabbit",
    "Calm and Relaxed 😌": "calm_owl",      
}
 
# -------------------- 2. HELPER FUNCTIONS (Data & Streak) (JOURNAL APP)
# --------------------
 
def get_user_data_file(user_name):
    """Generates a unique file name based on user name."""
    if not user_name:
        return None
    safe_name = user_name.strip().lower().replace(" ", "_")
    return f"diary_{safe_name}.json"
 
def create_initial_sprout_state(): 
    """Initializes the Mood Sprout state for a new user or on first run.""" 
    mood_keys = POTION_MAPPING.keys()
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    return {
        # Initial potion count is 5 for each (user request)
        'available_potions': {e: SPROUT_INITIAL_POTIONS for e in mood_keys}, 
        # Evolution counts start at 0
        'emotion_counts': {e: 0 for e in mood_keys},
        'total_feeds': 0,
        'evolution_threshold': SPROUT_EVOLUTION_THRESHOLD, 
        'evolved': False,
        # Daily potion logging
        'daily_potion_count': 0, 
        'last_potion_date': today_str
    }
 
def load_diary(user_name):
    """Loads diary data for the specified user."""
    data_file = get_user_data_file(user_name)
    if not data_file: return
    
    if os.path.exists(data_file):
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                st.session_state.diary = data.get("diary", {})
                st.session_state.total_points = data.get("total_points", 0)
                
                loaded_date = data.get("fortune_date")
                today_str = datetime.date.today().strftime("%Y-%m-%d")
                
                if loaded_date == today_str:
                    st.session_state.fortune_drawn = True
                    st.session_state.fortune_result = data.get("fortune_result", None)
                else:
                    st.session_state.fortune_drawn = False
                    st.session_state.fortune_result = None
            
                # --- Mood Sprout Game State Loading (using original key 'elf_state') ---
                st.session_state.elf_state = data.get("elf_state", None)
                if not st.session_state.elf_state:
                    st.session_state.elf_state = create_initial_sprout_state() 
                
                # --- Check and reset daily potion limit ---
                last_potion_date = st.session_state.elf_state.get('last_potion_date', '1900-01-01')
                if last_potion_date != datetime.date.today().strftime("%Y-%m-%d"):
                    st.session_state.elf_state['daily_potion_count'] = 0
                    st.session_state.elf_state['last_potion_date'] = datetime.date.today().strftime("%Y-%m-%d")
                    
        except json.JSONDecodeError:
            st.session_state.diary = {}
            st.session_state.elf_state = create_initial_sprout_state() 
    else:
        st.session_state.diary = {}
        st.session_state.elf_state = create_initial_sprout_state() 
 
def save_diary():
    """Saves diary and state data for the current user."""
    user_name = st.session_state.get("user_name")
    data_file = get_user_data_file(user_name)
    if not data_file: return
 
    data_to_save = {
        "diary": st.session_state.diary,
        "total_points": st.session_state.total_points,
        "user_name": user_name,
        "fortune_drawn": st.session_state.get("fortune_drawn", False),
        "fortune_result": st.session_state.get("fortune_result", None),
        "fortune_date": datetime.date.today().strftime("%Y-%m-%d"),
        # --- Mood Elf Game State Saving (using original key 'elf_state') ---
        "elf_state": st.session_state.elf_state
    }
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=4)
 
def calculate_streak(diary):
    """Calculates the current consecutive logging streak."""
    if not diary: return 0
    logged_dates = set(
        datetime.datetime.strptime(d, "%Y-%m-%d").date() 
        for d in diary.keys()
    )
    today = datetime.date.today()
    streak = 0
    day_to_check = today
    if day_to_check in logged_dates:
        streak = 1
        day_to_check -= datetime.timedelta(days=1)
    elif (day_to_check - datetime.timedelta(days=1)) in logged_dates:
        streak = 1
        day_to_check -= datetime.timedelta(days=2) 
    else:
        return 0
    while day_to_check in logged_dates:
        streak += 1
        day_to_check -= datetime.timedelta(days=1)
    return streak
 
# --- ACHIEVEMENT CALCULATION LOGIC ---
def calculate_achievements(diary, streak):
    """Checks the user's diary against predefined achievement thresholds."""
    total_entries = len(diary)
    logged_moods = set(entry['mood'] for entry in diary.values())
    unique_moods_count = len(logged_moods)
    
    unlocked_achievements = []
    
    for achievement in ACHIEVEMENTS:
        is_unlocked = False
        if achievement['type'] == 'total_entries' and total_entries >= achievement['threshold']:
            is_unlocked = True
        elif achievement['type'] == 'streak' and streak >= achievement['threshold']:
            is_unlocked = True
        elif achievement['type'] == 'unique_moods' and unique_moods_count >= achievement['threshold']:
            if achievement['threshold'] == len(MOOD_MAPPING):
                 is_unlocked = unique_moods_count >= achievement['threshold']
            else:
                 is_unlocked = unique_moods_count >= achievement['threshold']
            
        if is_unlocked:
            unlocked_achievements.append(achievement['name'])
            
    return unlocked_achievements

def get_diary_response(text):
    """Generates response based on keywords or random general."""
    text_lower = text.lower()
    for keyword, reply in EMOTION_RESPONSES.items(): 
        if keyword in text_lower:
            return reply
    return random.choice(GENERAL_RESPONSES)
 
def analyze_recent_mood_for_advice(diary):
    if not diary:
        return "👋 Time to start your first entry and unlock personalized advice!"
    today = datetime.date.today()
    one_week_ago = today - datetime.timedelta(days=7)
    recent_scores = []
    for date_str, entry in diary.items():
        entry_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        if one_week_ago <= entry_date < today:
            recent_scores.append(entry.get('score', 3))
    if not recent_scores:
        return "🤔 Need a week of data for personalized advice. Keep logging!"
    df = pd.Series(recent_scores)
    avg_score = df.mean()
    if avg_score <= 2.5:
        low_moods = [entry['mood'] for date_str, entry in diary.items() 
                     if one_week_ago <= datetime.datetime.strptime(date_str, "%Y-%m-%d").date() < today and entry.get('score', 3) <= 2]
        if low_moods:
            most_common_low_mood = pd.Series(low_moods).mode()[0]
            if most_common_low_mood in ["😢", "😥"]:
                return f"😥 Recent Mood Alert: You've often felt sad/anxious. **Challenge:** Try a 10-minute mindfulness exercise today."
            elif most_common_low_mood in ["😴"]:
                return f"😴 Recent Mood Alert: You've often felt tired. **Challenge:** Aim for 30 minutes of light physical activity today."
            elif most_common_low_mood in ["😡"]:
                return f"😡 Recent Mood Alert: You've often felt angry. **Challenge:** Write down 3 things you are grateful for before bed."
            else:
                return f"📉 Recent Mood Alert: Your average mood score is low. **Challenge:** Reach out to a friend or loved one today."
    elif avg_score >= 4.0:
        return "✨ Great Job! Your recent mood trend is excellent! **Advice:** Share your joy—compliment someone today!"
    else:
        return "⚖️ Your mood is balanced. **Advice:** Keep exploring your activities! Try adding one new tag today."
 
 
# -------------------- 3. MOOD SPROUT GAME LOGIC (JOURNAL APP)
# --------------------
 
def get_sprout_evolution_type(): 
    """Determines the sprout's evolution type based on the most fed potion.""" 
    plant_state = st.session_state.elf_state
    
    if not plant_state['evolved']:
        return "Seed" 
 
    # Find the emotion with the maximum feed count
    max_feed_count = -1
    evolution_type = "Happy" # Default Sprout Type
 
    for emotion, count in plant_state['emotion_counts'].items():
        if count > max_feed_count:
            max_feed_count = count
            # Convert lowercase emotion name to Capitalized name for image lookup
            evolution_type = emotion.capitalize() 
    
    if max_feed_count == 0:
        return "Happy" 
        
    return evolution_type
 
 
def feed_mood_sprout(emotion): 
    """Core logic to feed the sprout and check for evolution.""" 
    plant_state = st.session_state.elf_state
    
    if plant_state['evolved']:
        st.toast('The Mood Sprout has already evolved! No more feeding allowed.', icon="✨") 
        return
 
    # Ensure emotion name is lowercase for dictionary lookup
    emotion_name = emotion.lower()
    
    if plant_state['available_potions'][emotion_name] > 0:
        plant_state['available_potions'][emotion_name] -= 1
        plant_state['emotion_counts'][emotion_name] += 1
        plant_state['total_feeds'] += 1
        st.toast(f"Successfully fed {emotion_name.capitalize()} Potion! 🧪", icon="😋")
    else:
        st.toast(f"❌ {emotion_name.capitalize()} Potion ran out! Log your mood to get more.", icon="😔")
        
    if plant_state['total_feeds'] >= SPROUT_EVOLUTION_THRESHOLD: 
        plant_state['evolved'] = True
        st.balloons()
        
    st.session_state.elf_state = plant_state
    save_diary() # Save the updated sprout state
 
def grant_mood_potion(mood_emoji):
    """Grants a potion based on mood, checks daily limit."""
    plant_state = st.session_state.elf_state
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    # Daily reset check (safety)
    if plant_state.get('last_potion_date') != today_str:
        plant_state['daily_potion_count'] = 0
        plant_state['last_potion_date'] = today_str
 
    if plant_state['daily_potion_count'] < MAX_DAILY_POTION_ENTRIES:
        mood_name = EMOJI_TO_SPROUT_NAME.get(mood_emoji) 
        if mood_name:
            plant_state['available_potions'][mood_name] += 1
            plant_state['daily_potion_count'] += 1
            st.session_state.potion_granted_today = True # Mark as granted
            return mood_name.capitalize(), True
    
    return None, False
 
def reset_mood_sprout(): 
    """Resets the Mood Sprout's evolution state only.""" 
    plant_state = st.session_state.elf_state
    
    # Preserve potion counts, but reset feed counts
    emotion_keys = POTION_MAPPING.keys()
    
    st.session_state.elf_state.update({
        'emotion_counts': {e: 0 for e in emotion_keys},
        'total_feeds': 0,
        'evolved': False,
    })
    
    st.toast("Mood Sprout has been reset to Seed! Potions remain the same.", icon="🌱") 
    save_diary()

# -------------------- 3.5. PET GAME LOGIC (ADDED)
# --------------------

def handle_pet_interaction(action_type, prefix=""):
    """Handles click events for pet interaction buttons in the dedicated page."""
    
    # 使用專用的 session state key
    animal_id = st.session_state[prefix + 'pet_animal_id']
    animal = ANIMAL_COMPANIONS[animal_id]
    
    # Get a random response from the animal
    message = random.choice(animal["responses"][action_type])
    
    st.session_state[prefix + 'pet_animal_message'] = message
    
    # Rerun to update the display
    st.rerun()

def render_pet_app_content(prefix=""):
    """Renders the core pet interaction application components."""

    # --- Pet Game State Initialization ---
    
    # 為了防止與主 Journal 應用程式的 session state 衝突，我們使用 prefix
    if prefix + 'pet_mood_choice' not in st.session_state:
        st.session_state[prefix + 'pet_mood_choice'] = list(PET_MOOD_CHOICES.keys())[0] 
    if prefix + 'pet_animal_id' not in st.session_state:
        st.session_state[prefix + 'pet_animal_id'] = PET_MOOD_CHOICES[st.session_state[prefix + 'pet_mood_choice']]
    if prefix + 'pet_animal_message' not in st.session_state:
        initial_animal_id = st.session_state[prefix + 'pet_animal_id']
        st.session_state[prefix + 'pet_animal_message'] = ANIMAL_COMPANIONS[initial_animal_id]["initial_message"]
    
    # --- 1. Choose Today's Mood ---
    st.markdown("### ✅ Choose Your Current Mood:")
    
    selected_mood = st.radio(
        "Select a mood to summon your companion:",
        options=list(PET_MOOD_CHOICES.keys()),
        index=list(PET_MOOD_CHOICES.keys()).index(st.session_state[prefix + 'pet_mood_choice']),
        key=prefix + 'pet_mood_radio',
        horizontal=True
    )

    # Check if selection changed, if so, update animal and message
    if selected_mood != st.session_state[prefix + 'pet_mood_choice']:
        st.session_state[prefix + 'pet_mood_choice'] = selected_mood
        st.session_state[prefix + 'pet_animal_id'] = PET_MOOD_CHOICES[selected_mood]
        new_animal = ANIMAL_COMPANIONS[st.session_state[prefix + 'pet_animal_id']]
        st.session_state[prefix + 'pet_animal_message'] = new_animal["initial_message"]
        st.toast(f"You summoned the {new_animal['name']}!", icon="🎉")
        st.rerun()

    st.markdown("---")
    
    # --- 2. Display Animal and Response ---
    
    current_animal = ANIMAL_COMPANIONS[st.session_state[prefix + 'pet_animal_id']]
    
    st.markdown(f"### 💖 My Companion: {current_animal['name']}")
    
    # Get the animal's image path
    animal_image_filename = current_animal["art"]["visual_path"]

    col_art, col_response = st.columns([1, 2])
    
    with col_art:
        # Load image using PIL
        pet_image_pil = load_pet_image(animal_image_filename)
        if pet_image_pil:
            st.image(pet_image_pil, caption=f"Cute {current_animal['name']}", width=200)
        else:
            # Fallback if image still fails to load
            st.error(f"⚠️ Could not load image '{animal_image_filename}'. Please ensure the file is in the root folder.")


    with col_response:
        # Animal Response Block
        st.markdown(
            f"""
            <div style="padding: 15px; border-radius: 10px; border-left: 5px
solid #ffcc00; background-color: #fffacd;">
                **{current_animal['name']} whispers:** {st.session_state[prefix + 'pet_animal_message']}
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")

    # --- 3. Player Interaction Area ---
    st.markdown("### 👋 Interact with Your Companion")
    
    col_tap, col_pet, col_feed = st.columns(3)
    
    with col_tap:
        if st.button("👆 Tap It", key=prefix + "pet_tap_btn", use_container_width=True):
            handle_pet_interaction("tap", prefix)
            
    with col_pet:
        if st.button("🥰 Pet It", key=prefix + "pet_pet_btn", use_container_width=True):
            handle_pet_interaction("pet", prefix)
            
    with col_feed:
        if st.button("🍎 Feed It", key=prefix + "pet_feed_btn", use_container_width=True):
            handle_pet_interaction("feed", prefix)
            st.toast(f"{current_animal['name']} is eating happily!", icon="🍎")

# -------------------- 4. INITIALIZATION --------------------
 
def initialize_session_state():
    if "user_name" not in st.session_state:
        st.session_state.page = "onboarding"
    elif "page" not in st.session_state:
        st.session_state.page = "fortune_draw"
        
    if "selected_date" not in st.session_state:
        st.session_state.selected_date = datetime.date.today()
    if "selected_mood_emoji" not in st.session_state:
        st.session_state.selected_mood_emoji = None
    
    if "diary" not in st.session_state:
        st.session_state.diary = {}
    if "total_points" not in st.session_state:
        st.session_state.total_points = 0
        
    if "fortune_drawn" not in st.session_state:
        st.session_state.fortune_drawn = False
        st.session_state.fortune_result = None
        
    # --- Mood Sprout Game State Initialization (using original key 'elf_state') ---
    if "elf_state" not in st.session_state:
        st.session_state.elf_state = create_initial_sprout_state() 
    
    if "potion_granted_today" not in st.session_state:
        st.session_state.potion_granted_today = False
    
    if "unlocked_achievements" not in st.session_state: # NEW: Achievement state
        st.session_state.unlocked_achievements = []

    # Ensure daily count is reset on a new day
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    if st.session_state.elf_state.get('last_potion_date') != today_str:
        st.session_state.elf_state['daily_potion_count'] = 0
        st.session_state.elf_state['last_potion_date'] = today_str
 
initialize_session_state() 
 
# -------------------- 5. STYLES 
# --------------------
 
FIXED_THEME_COLOR = "#c9b9a8" 
FIXED_ACCENT_COLOR = "#4b3f37" 
 
st.markdown(f"""
    <style>
        /* Journal Pro Styles */
        /* **修正：將背景設定為米白色，並移除所有圖片背景相關的 CSS** */
        .stApp {{
            background-color: {BACKGROUND_COLOR}; /* Linen 米白色 */
        }}
        
        .title {{
            text-align: center;
            font-size: 36px;
            font-weight: bold;
            color: {FIXED_ACCENT_COLOR}; 
            margin-bottom: 10px;
        }}
        .subtitle {{
            text-align: center;
            font-size: 18px;
            color: #6d5f56;
            margin-bottom: 25px;
        }}
        .fortune-result-box {{
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            text-align: center;
            background-color: #fff8e1; /* Light yellow background */
            margin-top: 20px;
        }}
        .fortune-level {{
            font-size: 40px;
            font-weight: bold;
            color: {FIXED_ACCENT_COLOR};
        }}
        .fortune-emoji {{
            font-size: 60px;
            margin: 10px 0;
        }}
        .fortune-description {{
            font-size: 18px;
            font-style: italic;
            color: #6d5f56;
        }}
        .shaking-container {{
            text-align: center;
            margin: 40px auto;
            max-width: 300px;
        }}
        .shaking-icon {{
            font-size: 100px;
            display: inline-block;
        }}
        /* --- Mood Sprout Game Styles (Visual UI) --- */ 
        @keyframes bounce {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-15px); }}
        }}
 
        .plant-image-animated {{ 
            animation: bounce 2s infinite ease-in-out;
        }}
        /* Potion and Pet Display Styles */
        .potion-item {{ 
            display: flex; 
            align-items: center; 
            margin-bottom: 10px;
            gap: 10px; 
        }}
        .potion-img {{
            width: 30px; 
            height: 30px;
            object-fit: contain;
        }}
        .potion-item > div:last-child {{
            flex-grow: 1; 
        }}
        /* NEW: Achievement styles */
        .achievement-icon-gold {{
            font-size: 2em;
            color: gold; 
            margin-right: 10px;
        }}
        .achievement-icon-grey {{
            font-size: 2em;
            color: #9e9e9e; 
            margin-right: 10px;
        }}
        /* Custom styles for the new Pet Partner Button in action_page */
        .stButton button[key*="pet_partner_btn_action"] {{
            /* 修正 NameError: 確保所有 CSS 語法正確 */
            border: 2px solid #ff69b4; /* Pink border */
            color: #ff69b4;
            font-weight: bold;
        }}
        .stButton button[key*="pet_partner_btn_action"]:hover {{
            background-color: #ffe4e1; /* Light pink hover */
        }}
    </style>
""", unsafe_allow_html=True)
 
 
# -------------------- 6. PAGE FUNCTIONS 
# --------------------
 
def render_onboarding_page():
    st.markdown("<div class='title'>Welcome to Your Mood Journal!</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Let's start by entering your name to load your journal.</div>", unsafe_allow_html=True)
 
    with st.container():
        name = st.text_input("Enter your name:", key="name_input")
        
        if st.button("Start Journaling 🚀", use_container_width=True):
            if name:
                st.session_state.user_name = name.strip()
                load_diary(st.session_state.user_name)
                st.session_state.page = "fortune_draw"
                st.rerun() 
            else:
                st.warning("Please enter your name to proceed.")
 
 
def render_fortune_draw_page():
    user = st.session_state.user_name
    st.markdown(f"<div class='title'>⛩️ Daily Fortune Draw</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='subtitle'>Welcome back, {user}! Draw your fortune to guide your day.</div>", unsafe_allow_html=True)
    
    draw_container = st.empty()
    
    if not st.session_state.fortune_drawn:
        draw_container.markdown(
            f"<div class='shaking-container'><div class='shaking-icon'>🎋</div></div>",
            unsafe_allow_html=True
        )
        
        if st.button("🥠 Draw Your Destiny! (Daily Draw)", use_container_width=True):
            for i in range(5):
                icon = "🎍" if i % 2 == 0 else "🎋"
                draw_container.markdown(
                    f"<div class='shaking-container'><div class='shaking-icon'>{icon}</div></div>", 
                    unsafe_allow_html=True
                )
                time.sleep(0.05) 
 
            fortune = random.choice(FORTUNE_SLIPS)
            st.session_state.fortune_result = fortune
            st.session_state.fortune_drawn = True
            save_diary()
            st.balloons()
            st.rerun() 
        
    
    if st.session_state.fortune_drawn and st.session_state.fortune_result:
        level, emoji, description = st.session_state.fortune_result
        
        draw_container.empty()
        
        st.markdown("---")
        st.markdown(f"### ✨ Your Daily Guidance for {datetime.date.today().strftime('%Y-%m-%d')}")
        
        st.markdown("<div class='fortune-result-box'>", unsafe_allow_html=True)
        st.markdown(f"<div class='fortune-level'>{level}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='fortune-emoji'>{emoji}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='fortune-description'>{description}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        if st.button("Start Journaling for Today 📝", use_container_width=True):
            st.session_state.page = "date"
            st.rerun()
 
    elif st.session_state.fortune_drawn:
        st.info("You have already drawn your fortune for today. Please start journaling!")
        if st.button("Go to Journal 📝", use_container_width=True):
            st.session_state.page = "date"
            st.rerun()
 
 
def render_date_page():
    user = st.session_state.user_name
    points = st.session_state.total_points
    current_streak = calculate_streak(st.session_state.diary) 
    
    st.markdown(f"<div class='title'>🌸 Hi, {user}!</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='subtitle'>🔥 **Streak:** {current_streak} days | ⭐ **Mood Points:** {points} | Select a date to begin your entry.</div>", unsafe_allow_html=True)
    
    if st.session_state.fortune_result:
        level, emoji, _ = st.session_state.fortune_result
        st.success(f"🔮 Today's Fortune: **{level} {emoji}** - Use this guidance for your entry!")
 
    advice = analyze_recent_mood_for_advice(st.session_state.diary)
    st.markdown(f"<div class='advice-box'>💡 **Today's Insight:** {advice}</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    selected_date = st.date_input("📅 Choose a date:", value=st.session_state.selected_date, key="date_picker")
    st.session_state.selected_date = selected_date
    st.markdown("---")
    
    # ************ 根據需求 1 調整：只保留 Next/Edit Mood 按鈕 ************
    col1, col2, col3, col4, col5 = st.columns(5)
    date_key = selected_date.strftime("%Y-%m-%d")
    is_logged = date_key in st.session_state.diary
    button_text = "Next ➜ Edit/Choose Mood" if is_logged else "Next ➜ Choose Mood"
    
    if col1.button(button_text, use_container_width=True):
        st.session_state.page = "mood"
        st.rerun()
        
    # **移除其他按鈕以符合需求 1**
    # if col2.button("📆 View Calendar", use_container_width=True):
    #     st.session_state.page = "calendar"
    #     st.rerun()
    # if col3.button("🔮 View Insights", use_container_width=True):
    #     st.session_state.page = "insight"
    #     st.rerun()
    # if col4.button("🌱 Mood Sprout", use_container_width=True): 
    #     st.session_state.page = "mood_sprout" 
    #     st.rerun()
    # if col5.button("🏆 Achievements", use_container_width=True): 
    #     st.session_state.page = "rewards"
    #     st.rerun()
 
 
def render_mood_page():
    date_key = st.session_state.selected_date.strftime("%Y-%m-%d")
    st.markdown("<div class='title'>How do you feel, today?</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='subtitle'>{date_key}</div>", unsafe_allow_html=True)
    current_mood = st.session_state.diary.get(date_key, {}).get("mood", None)
    if current_mood and st.session_state.selected_mood_emoji is None:
        st.session_state.selected_mood_emoji = current_mood
    cols = st.columns(len(MOOD_MAPPING))
    for i, (mood_name, emoji) in enumerate(MOOD_MAPPING.items()):
        is_selected = (emoji == st.session_state.selected_mood_emoji)
        if cols[i].button(f"{emoji} {mood_name} {'(Selected)' if is_selected else ''}", key=mood_name, use_container_width=True):
            st.session_state.selected_mood_emoji = emoji
            st.session_state.page = "journal"
            st.rerun()
    st.markdown("---")
    if st.button("⬅ Back to Date"):
        st.session_state.page = "date"
        st.rerun()
 
def render_journal_page():
    date_key = st.session_state.selected_date.strftime("%Y-%m-%d")
    mood_icon = st.session_state.selected_mood_emoji
    existing_entry = st.session_state.diary.get(date_key, {})
    initial_text = existing_entry.get("text", "")
    initial_tags = existing_entry.get("tags", [])
    st.markdown(f"<div class='title'>📝 Journal Entry for {date_key}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='subtitle'>Your mood: {mood_icon}</div>", unsafe_allow_html=True)
    prompt_seed = st.session_state.selected_date.toordinal()
    random.seed(prompt_seed)
    daily_prompt = random.choice(DAILY_PROMPTS)
    random.seed() 
    st.info(f"✨ **Today's Prompt:** {daily_prompt}")
    selected_tags = st.multiselect(
        "🏷️ **Select relevant activities/causes:** (Optional)", 
        options=ACTIVITY_TAGS, 
        default=initial_tags,
        key="activity_tags"
    )
    diary_text = st.text_area("Write about your day:", value=initial_text, height=200, key="diary_text_area")
    col1, col2 = st.columns(2)
    if col1.button("💾 Save & Get Reflection", use_container_width=True):
        response = get_diary_response(diary_text)
        reward_points = 0
        is_new_entry = date_key not in st.session_state.diary
        
        # Check and grant potion
        potion_reward_name, is_granted = grant_mood_potion(mood_icon)
        
        if is_new_entry:
            reward_points = POINTS_PER_ENTRY
            st.session_state.total_points += reward_points
            
        st.session_state.diary[date_key] = {
            "mood": mood_icon, 
            "text": diary_text, 
            "response": response,
            "score": MOOD_SCORES.get(mood_icon, 3),
            "tags": selected_tags
        }
        save_diary()
        
        st.session_state.page = "action_page"
        st.session_state.last_response = response
        st.session_state.reward_points = reward_points
        st.session_state.potion_reward_name = potion_reward_name
        st.session_state.potion_is_granted = is_granted
        st.rerun()
        
    if col2.button("⬅ Back to Mood", use_container_width=True):
        st.session_state.page = "mood"
        st.rerun()
    if 'response' in existing_entry:
        st.markdown(f"---")
        st.markdown(f"### 💬 Last Reflection:\n*{existing_entry['response']}*")
 
def render_action_page():
    # ************ 根據需求 2 調整：這是日記完成後顯示所有 ICON 的頁面 ************
    st.markdown("<div class='title'>Entry Saved Successfully!</div>", unsafe_allow_html=True)
    
    # Display potion grant message
    if st.session_state.potion_is_granted:
        st.success(f"🧪 Potion Reward! You earned one **{st.session_state.potion_reward_name}** Potion!\n\n**Today's Potion Count:** {st.session_state.elf_state.get('daily_potion_count', 0)} / {MAX_DAILY_POTION_ENTRIES}")
    else:
        st.info(f"😔 Daily potion limit reached (Max: {MAX_DAILY_POTION_ENTRIES} potions). Try again tomorrow!")
        
    if st.session_state.reward_points > 0:
        st.balloons()
        st.success(f"🎉 **Reward!** You earned **{st.session_state.reward_points} Mood Points** for your first entry today!")
        
    st.markdown(f"### 🌈 Today's Reflection:\n*{st.session_state.last_response}*")
    
    if random.random() < 0.25: 
        st.markdown("---")
        st.markdown("### 🔮 Daily Surprise:")
        st.warning(random.choice(SURPRISE_FACTS))
        
    st.markdown("---")
    st.markdown("### What would you like to do next?")
    
    # ************ 這裡顯示所有 ICON，並新增日曆按鈕 ************
    col1, col2, col3, col4, col5 = st.columns(5)
    
    if col1.button("🔮 View Insights", key="insights_btn_action", use_container_width=True):
        st.session_state.page = "insight"
        st.rerun()
    if col2.button("🏆 View Achievements", key="achievements_btn_action", use_container_width=True): 
        st.session_state.page = "rewards"
        st.rerun()
    if col3.button("📆 View Calendar", key="calendar_btn_action", use_container_width=True): # **新增日曆按鈕**
        st.session_state.page = "calendar"
        st.rerun()
    if col4.button("🌱 Feed Mood Sprout", key="sprout_btn_action", use_container_width=True): 
        st.session_state.page = "mood_sprout" 
        st.rerun()
        
    # ************ 新增的 "Healing Pet Partner" 按鈕 ************
    if col5.button("💖 Healing Pet Partner", key="pet_partner_btn_action", use_container_width=True):
        st.session_state.page = "healing_pet_partner" 
        st.rerun()
        
    st.markdown("---")
    # **保留一個開始新日誌的按鈕，導向 date 頁面 (用於開始新一天的日誌)**
    if st.button("📝 Start New Entry (Select Another Date)", key="new_entry_btn_bottom", use_container_width=True):
        st.session_state.selected_date = datetime.date.today()
        st.session_state.selected_mood_emoji = None
        st.session_state.page = "date"
        st.rerun()
 
 
def render_calendar_page():
    st.markdown("<div class='title'>📆 Monthly Mood Calendar</div>", unsafe_allow_html=True)
    
    today = datetime.date.today()
    if 'cal_year' not in st.session_state:
        st.session_state.cal_year = today.year
    if 'cal_month' not in st.session_state:
        st.session_state.cal_month = today.month
        
    # Month/Year Navigation
    col_prev, col_current, col_next = st.columns([1, 2, 1])
    if col_prev.button("⬅ Previous Month", use_container_width=True):
        st.session_state.cal_month -= 1
        if st.session_state.cal_month < 1:
            st.session_state.cal_month = 12
            st.session_state.cal_year -= 1
        st.rerun()
    if col_next.button("Next Month ➡", use_container_width=True):
        st.session_state.cal_month += 1
        if st.session_state.cal_month > 12:
            st.session_state.cal_month = 1
            st.session_state.cal_year += 1
        st.rerun()
    col_current.markdown(f"<h3 style='text-align: center;'>{calendar.month_name[st.session_state.cal_month]} {st.session_state.cal_year}</h3>", unsafe_allow_html=True)
 
    # Days of the week header
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    cols_header = st.columns(7)
    for i, day in enumerate(day_names):
        cols_header[i].markdown(f"**<div style='text-align: center; color: {FIXED_ACCENT_COLOR};'>{day}</div>**", unsafe_allow_html=True)
 
    # Date cells
    cal = calendar.Calendar()
    month_data = cal.monthdatescalendar(st.session_state.cal_year, st.session_state.cal_month)
    
    for week in month_data:
        cols_week = st.columns(7)
        for i, date in enumerate(week):
            date_key = date.strftime("%Y-%m-%d")
            entry = st.session_state.diary.get(date_key)
            
            mood_emoji = entry.get("mood", "📝") if entry else ""
            mood_tip = f"Entry: {date_key}\nMood: {mood_emoji}\nTags: {', '.join(entry.get('tags', []))}" if entry else f"No entry for {date_key}"
            
            # Formatting for dates outside the current month
            is_current_month = date.month == st.session_state.cal_month
            date_color = FIXED_ACCENT_COLOR if is_current_month else "#aaa"
            
            date_display = date.day
            
            # Highlight today's date
            if date == today:
                date_display = f"**{date.day}**"
                date_color = "green"
            
            content = f"<div style='text-align: center; color: {date_color}; padding: 5px; border-radius: 5px; border: 1px solid {'#ddd' if is_current_month else 'transparent'};'>"
            content += f"<span title='{mood_tip}'>{date_display}</span><br/>"
            content += f"<span style='font-size: 20px;'>{mood_emoji}</span>"
            content += "</div>"
 
            cols_week[i].markdown(content, unsafe_allow_html=True)
 
    st.markdown("---")
    # ************ 根據需求 2 調整：返回到 action_page ************
    if st.button("⬅ Back to Action Page"):
        st.session_state.page = "action_page"
        st.rerun()
 
 
def render_insight_page():
    # --- INSIGHTS PAGE ---
    user = st.session_state.user_name
    st.markdown(f"<div class='title'>🔮 {user}'s Fun Mood Insights</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Analyze your mood trends and patterns.</div>", unsafe_allow_html=True)
    
    if not st.session_state.diary:
        st.warning("Please make at least one journal entry to view insights!")
        if st.button("⬅ Back to Action Page"): # **修改返回按鈕**
            st.session_state.page = "action_page"
            st.rerun()
        return

    # Prepare DataFrame
    diary_df = pd.DataFrame.from_dict(st.session_state.diary, orient='index')
    diary_df.index.name = 'Date'
    diary_df = diary_df.reset_index()
    diary_df['Date'] = pd.to_datetime(diary_df['Date'])
    diary_df = diary_df.sort_values(by='Date')

    st.markdown("---")
    
    ## 1. Overall Metrics
    col_e, col_s, col_p = st.columns(3)
    col_e.metric("Total Entries", len(diary_df))
    col_s.metric("Current Streak", calculate_streak(st.session_state.diary))
    col_p.metric("Total Mood Points", st.session_state.total_points)

    st.markdown("---")
    
    ## 2. Mood Trend Over Time
    st.markdown("### 📈 Mood Score Trend (Last 30 Days)")
    if 'score' in diary_df.columns and 'Date' in diary_df.columns:
        today = datetime.date.today()
        thirty_days_ago = today - datetime.timedelta(days=30)
        recent_df = diary_df[diary_df['Date'].dt.date >= thirty_days_ago].copy()
        
        if not recent_df.empty:
            recent_df.rename(columns={'score': 'Mood Score'}, inplace=True)
            
            fig = px.line(
                recent_df, 
                x='Date', 
                y='Mood Score',
                title='Mood Score Trend Over Past 30 Days',
                labels={'Date': 'Date', 'Mood Score': 'Score'},
                line_shape='spline',
            )
            fig.update_yaxes(range=[1, 5]) 
            st.plotly_chart(fig, use_container_width=True)
            
            avg_score = recent_df['Mood Score'].mean()
            st.info(f"💡 **Average Score (Past 30 Days):** {avg_score:.2f} / 5.0")
        else:
            st.info("Not enough data in the last 30 days to plot a trend.")

    st.markdown("---")
    
    ## 3. Top Activity Correlation
    st.markdown("### 💖 Activity Correlation & Frequency")
    
    all_tags = []
    tag_scores = {}
    
    for _, row in diary_df.iterrows():
        score = row.get('score', 3)
        for tag in row.get('tags', []):
            all_tags.append(tag)
            tag_scores[tag] = tag_scores.get(tag, []) + [score]
            
    if all_tags:
        # Calculate Average Score per Tag
        avg_scores = {tag: sum(scores) / len(scores) for tag, scores in tag_scores.items()}
        avg_df = pd.Series(avg_scores).sort_values(ascending=False).to_frame(name='Avg Mood Score')
        
        # Calculate Tag Frequency
        tag_counts = pd.Series(all_tags).value_counts()
        tag_freq_df = tag_counts.to_frame(name='Frequency')

        # Combine for display
        combined_df = avg_df.join(tag_freq_df, how='outer')
        combined_df.index.name = "Activity Tag"
        
        st.info("Higher average scores suggest these activities are associated with better moods.")
        st.dataframe(combined_df, use_container_width=True)
    else:
        st.info("Start using **Activity Tags** in your entries to unlock correlation analysis!")

    st.markdown("---")
    
    # ************ 根據需求 2 調整：返回到 action_page ************
    if st.button("⬅ Back to Action Page"):
        st.session_state.page = "action_page"
        st.rerun()

# --- REWARDS PAGE ---
def render_rewards_page():
    user = st.session_state.user_name
    points = st.session_state.total_points
    current_streak = calculate_streak(st.session_state.diary)
    unlocked_achievements = calculate_achievements(st.session_state.diary, current_streak)
    
    st.markdown(f"<div class='title'>🏆 {user}'s Achievements & Rewards</div>", unsafe_allow_html=True)
    st.markdown(f"### ⭐ Mood Points: **{points}**")
    st.markdown("---")
    
    st.markdown("### 🏅 Achievements Log")
    
    if not unlocked_achievements:
        st.info("Keep journaling to unlock your first achievement!")

    for ach in ACHIEVEMENTS:
        is_unlocked = ach['name'] in unlocked_achievements
        
        if is_unlocked:
            icon_html = f'<span class="achievement-icon-gold">🏆</span>' 
        else:
            icon_html = f'<span class="achievement-icon-grey">🔗</span>'

        st.markdown(f"""
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                {icon_html}
                <div>
                    <div style="font-weight: bold; color: {FIXED_ACCENT_COLOR};">{ach['name']}</div>
                    <div style="font-size: 0.9em; color: #6d5f56;">{ach['desc']}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.info("Tip: More rewards and customization options coming soon!")
    
    # ************ 根據需求 2 調整：返回到 action_page ************
    if st.button("⬅ Back to Action Page", use_container_width=True):
        st.session_state.page = "action_page"
        st.rerun()

def render_mood_sprout_page(): 
    # --- Mood Sprout Game UI (Visual/Graphic) ---
    st.markdown("<div class='title'>🌱 Mood Sprout Game</div>", unsafe_allow_html=True) 
    
    plant_state = st.session_state.elf_state
    
    # Get current sprout status and image
    evolution_type = get_sprout_evolution_type() 
    image_path = PET_MAPPING.get(evolution_type, PET_MAPPING["Seed"]) 
    
    # Load image for display
    plant_image_pil = load_pet_image(image_path)
    
    # Progress Display 
    if SPROUT_EVOLUTION_THRESHOLD > 0:
        # Use min(1.0, ...) to ensure value is between 0.0 and 1.0
        progress_percent = min(1.0, plant_state['total_feeds'] / SPROUT_EVOLUTION_THRESHOLD)
    else:
        progress_percent = 0.0
        
    # Progress bar text
    st.progress(progress_percent, text=f"Evolution Progress: **{plant_state['total_feeds']} / {SPROUT_EVOLUTION_THRESHOLD}** feeds")

    # Sprout Image Container
    col_img, col_status = st.columns([1, 2])
    
    # --- Left Image and Status ---
    with col_img:
        # Display status text (Status: Seed/Evolved...)
        if evolution_type == "Seed":
            st.markdown(f"**Status: Seed**")
            caption_text = f"Total Feeds: {plant_state['total_feeds']} / {SPROUT_EVOLUTION_THRESHOLD}"
        else:
            st.markdown(f"**Status: Evolved {evolution_type}**")
            caption_text = f"Max Feed Type: {evolution_type}"
            
        if plant_image_pil:
            if evolution_type == "Seed": 
                st.image(plant_image_pil, use_container_width=True, caption=caption_text)
            else:
                st.markdown(f'<div class="plant-image-animated">', unsafe_allow_html=True)
                st.image(plant_image_pil, use_container_width=True, caption=caption_text)
                st.markdown(f'</div>', unsafe_allow_html=True)
        else:
            st.warning(f"Image not found at: {image_path}")
            
        # Reset Button
        st.markdown("---")
        if st.button("♻ Reset Sprout to Seed", key="reset_sprout", use_container_width=True): 
            reset_mood_sprout() 
            st.rerun()
    
    # --- Right Potion Inventory ---
    with col_status:
        st.markdown("### 🧪 Your Potion Inventory")

        # Organize potion data into a DataFrame for display
        potion_data = {
            "Potion Type": [e.capitalize() for e in POTION_MAPPING.keys()],
            "Stock": [plant_state['available_potions'][e] for e in POTION_MAPPING.keys()],
            "Times Fed": [plant_state['emotion_counts'][e] for e in POTION_MAPPING.keys()],
        }
        potion_df = pd.DataFrame(potion_data)
        # Remove index column
        st.table(potion_df.set_index('Potion Type'))


    # --- Feeding Buttons ---
    st.markdown("---")
    st.markdown("### 🍴 Select Potion to Feed")
    
    emotion_keys = list(POTION_MAPPING.keys())
    feed_cols = st.columns(3) # Use three columns for buttons
    
    for i, emotion_name in enumerate(emotion_keys):
        count = plant_state['available_potions'][emotion_name]
        display_name = emotion_name.capitalize()
        potion_path = POTION_MAPPING.get(emotion_name)
        
        # Display in the corresponding column
        with feed_cols[i % 3]: 
            # **修正 NameError: 移除 border=True**
            with st.container(): 
                col_img_btn, col_txt_btn = st.columns([1, 4]) 
                
                with col_img_btn:
                    potion_image_pil = load_pet_image(potion_path) 
                    if potion_image_pil:
                        st.image(potion_image_pil, use_container_width=True) 
                        
                with col_txt_btn:
                    # **Keep button text complete (Feed... in stock)**
                    button_label = f"Feed {display_name} Potion ({count} in stock)"
                    
                    if st.button(button_label, 
                                 key=f"feed_btn_{emotion_name}", 
                                 use_container_width=True, 
                                 disabled=plant_state['evolved'] or count == 0):
                        feed_mood_sprout(emotion_name)
                        st.rerun()
                        
    st.markdown("---")
    
    # Bottom tips
    if plant_state['evolved']:
        st.success(f"🎉 **CONGRATULATIONS!** Your Mood Sprout has evolved into the **{evolution_type}** form!")
    elif plant_state['total_feeds'] > 0:
        st.info(f"Keep feeding! You need **{SPROUT_EVOLUTION_THRESHOLD - plant_state['total_feeds']}** more feeds to see your sprout grow.")
    else:
        st.info("Start logging your mood to earn potions, then feed your Mood Sprout to make it grow!")
        
    st.markdown("---")
    # ************ 根據需求 2 調整：返回到 action_page ************
    if st.button("⬅ Back to Action Page", key="back_from_sprout"):
        st.session_state.page = "action_page"
        st.rerun()

# --- NEW PET GAME PAGE FUNCTION ---
def render_healing_pet_partner_page():
    st.markdown("<div class='title'>💖 Healing Pet Partner</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>A cheerful companion based on your chosen mood. Interact and enjoy!</div>", unsafe_allow_html=True)
    
    # 渲染寵物互動應用程式的內容
    # 這裡使用 'pet_' prefix 來區分 session state
    render_pet_app_content(prefix="pet_")
    
    st.markdown("---")
    # ************ 根據需求 2 調整：返回到 action_page ************
    if st.button("⬅ Back to Action Page", key="back_from_pet_app"):
        st.session_state.page = "action_page"
        st.rerun()
 
# -------------------- 7. PAGE NAVIGATION --------------------
 
if st.session_state.page == "onboarding":
    render_onboarding_page()
elif st.session_state.page == "fortune_draw":
    render_fortune_draw_page()
elif st.session_state.page == "date":
    render_date_page()
elif st.session_state.page == "mood":
    render_mood_page()
elif st.session_state.page == "journal":
    render_journal_page()
elif st.session_state.page == "action_page":
    render_action_page()
elif st.session_state.page == "calendar":
    render_calendar_page()
elif st.session_state.page == "insight":
    render_insight_page() 
elif st.session_state.page == "mood_sprout": 
    render_mood_sprout_page()
elif st.session_state.page == "rewards":
    render_rewards_page()
# ************ 新增的頁面導航 ************
elif st.session_state.page == "healing_pet_partner":
    render_healing_pet_partner_page()