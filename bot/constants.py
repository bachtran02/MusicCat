BASE_YT_URL = 'https://www.youtube.com'

COLOR_DICT = {
    'RED':      0xd25557,
    'BLUE':     0x00E7FF ,
    'YELLOW':   0xffff5c,
    'GREEN':    0x76ffa1,
}

EFFECT_NIGHTCORE = {
    'equalizer': {
        'bands': [
            (0, -0.075),    (1, 0.125),    (2, 0.125)
        ],
    },
    'timescale': {
        'pitch':    0.95,
        'rate':     1.3,
        'speed':    1,
    }
}

EFFECT_BASS_BOOST = {
    'equalizer': {
        'bands': [
            ( 0,  0.2 ),    ( 1,  0.15),    ( 2,  0.1 ), 
            ( 3,  0.05),    ( 4,  0.0 ),    ( 5, -0.05), 
            ( 6, -0.1 ),    ( 7, -0.1 ),    ( 8, -0.1 ),
            ( 9, -0.1 ),    (10, -0.1 ),    (11, -0.1 ),
            (12, -0.1 ),    (13, -0.1 ),    (14, -0.1 ),
        ],
    } 
}


EMOJI_RESUME_PLAYER = '<:mc_resume:1187705966263812218>'
EMOJI_PAUSE_PLAYER  = '<:mc_pause:1187705962358902806>'
EMOJI_STOP_PLAYER   = '<:mc_stop:1187705975638081557>'
EMOJI_PLAY_PREVIOUS = '<:mc_previous:1187705971070488627>'
EMOJI_PLAY_NEXT     = '<:mc_next:1187705968331591710>'
EMOJI_RADIO_BUTTON  = '<:mc_radio_button:1187818871072247858>'
EMOJI_LOOP_OFF      = '<:mc_loop_off:1189020553353371678>'
EMOJI_LOOP_TRACK    = '<:mc_loop_track:1189020551340114032>'
EMOJI_LOOP_QUEUE    = '<:mc_loop_queue:1189020548525735956>'
EMOJI_SHUFFLE_OFF   = '<:mc_shuffle_off:1189022239354531890>'
EMOJI_SHUFFLE_ON    = '<:mc_shuffle_on:1189022235621605498>'