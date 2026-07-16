"""Content library: ambient lines, micro-practices, guided session scripts.

On real hardware this is the pre-loaded library the local LLM selects from
(and extends). Everything here is static text; llm.py does the selecting.
"""

# ---------------------------------------------------------------- ambient ---
# Ambient lines by day phase. (text, attribution-or-None)
AMBIENT = {
    "morning": [
        ("Begin when you're ready.", None),
        ("The day is wide. Nothing is owed yet.", None),
        ("Drink your tea slowly, as if it is the axis\non which the earth revolves.", "Thich Nhat Hanh"),
        ("What would make today feel unhurried?", None),
    ],
    "focus": [
        ("One thing at a time is enough.", None),
        ("The quieter you become,\nthe more you can hear.", "Ram Dass"),
        ("Attention is the rarest and purest\nform of generosity.", "Simone Weil"),
        ("This hour belongs to one thing.", None),
    ],
    "midday": [
        ("Half the day is a good place to pause.", None),
        ("Walk as if you are kissing\nthe earth with your feet.", "Thich Nhat Hanh"),
        ("The body keeps better time than the mind.", None),
    ],
    "afternoon": [
        ("How are you right now, Alexey?", None),
        ("Tension is who you think you should be.\nRelaxation is who you are.", "Chinese proverb"),
        ("Between stimulus and response there is a space.", "Viktor Frankl"),
        ("Nothing on this screen is urgent.", None),
    ],
    "evening": [
        ("The day is folding itself up.", None),
        ("What was one small good thing today?", None),
        ("At the still point of the turning world,\nthere the dance is.", "T. S. Eliot"),
        ("Enough, now.", None),
    ],
    "night": [
        ("", None),  # night mode is clock-only
    ],
}

# ------------------------------------------------------- micro-practices ---
# 30s–3min invitations. `speech` is spoken if the user accepts (taps the lid).
MICRO_PRACTICES = [
    {
        "title": "Three breaths",
        "body": "In through the nose, slow.\nOut a little longer than in.",
        "speech": [
            (0.0, "Let's take three breaths together."),
            (3.0, "Breathe in... slowly."),
            (5.0, "And out... a little longer."),
            (6.0, "Again. In..."),
            (5.0, "...and out."),
            (6.0, "One more. In..."),
            (5.0, "...and let it all the way out."),
            (5.0, "That's it. Back to your day."),
        ],
    },
    {
        "title": "Grounding",
        "body": "Feel your feet on the floor.\nThe chair holding your weight.",
        "speech": [
            (0.0, "For a moment, notice your feet on the floor."),
            (6.0, "The weight of your body in the chair."),
            (6.0, "The room around you, just as it is."),
            (7.0, "Good. Continue when you're ready."),
        ],
    },
    {
        "title": "Soften",
        "body": "Unclench the jaw.\nDrop the shoulders.",
        "speech": [
            (0.0, "Notice your jaw. Let it soften."),
            (6.0, "Your shoulders. Let them drop."),
            (6.0, "Your hands. Let them rest."),
            (7.0, "Carry this ease with you."),
        ],
    },
]

# ------------------------------------------------------- guided sessions ---
# Segments: (pause_before_seconds, spoken_text or None for held silence)
SESSIONS = {
    "settling": {
        "name": "A short settling",
        "minutes": 3,
        "anchor": "See. Hear. Feel.",
        "script": [
            (2.0, "Welcome. There's nothing to get right here."),
            (5.0, "Sit however you're comfortable, and let your eyes rest, open or closed."),
            (8.0, "Start by simply seeing. Notice one thing in your field of vision."),
            (10.0, "Now hearing. Notice the farthest sound you can find."),
            (12.0, "And feeling. Notice the breath, wherever it's most obvious."),
            (12.0, None),
            (10.0, "See. Hear. Feel. Let attention drift between them, unhurried."),
            (20.0, None),
            (12.0, "If the mind wandered, that's fine. That was the practice."),
            (10.0, None),
            (8.0, "In your own time, let the eyes refocus."),
            (6.0, "The day is still here. You're a little more here for it."),
        ],
        "reflection": "What is different, if anything?",
    },
    "metta": {
        "name": "Evening metta",
        "minutes": 4,
        "anchor": "May you be at ease.",
        "script": [
            (2.0, "This is a practice of goodwill. We'll keep it simple."),
            (6.0, "Bring to mind someone easy to care about."),
            (8.0, "Quietly, in your own words: may you be safe. May you be well."),
            (10.0, "May you be at ease."),
            (14.0, None),
            (8.0, "Now include yourself. The same words, the same tone."),
            (10.0, "May I be safe. May I be well. May I be at ease."),
            (16.0, None),
            (8.0, "Let the words go, and rest in whatever remains."),
            (12.0, None),
            (6.0, "That's the whole practice. Goodnight comes easier after this."),
        ],
        "reflection": "Carry it lightly.",
    },
}

# ------------------------------------------------------------ email pool ---
# The shell injects these through the simulated IMAP bridge.
EMAIL_SAMPLES = {
    "urgent": [
        {"sender": "Jean-Louis Moreau", "subject": "DFM review — need your call on enclosure tooling by EOD",
         "body": "Alexey, the tooling quote expires today. Two options attached..."},
        {"sender": "Pauline Bertry", "subject": "Investor call moved to 4pm TODAY — can you make it?",
         "body": "Sorry for the short notice, they had a conflict..."},
    ],
    "later": [
        {"sender": "Waveshare Support", "subject": "Re: partial refresh LUT for 7.5inch panel",
         "body": "Hello, please find the updated waveform file..."},
    ],
    "noise": [
        {"sender": "Hacker Newsletter", "subject": "#712: The best links of the week",
         "body": "This week: yet another JS framework..."},
        {"sender": "LinkedIn", "subject": "You appeared in 12 searches this week",
         "body": "See who's looking..."},
    ],
}
