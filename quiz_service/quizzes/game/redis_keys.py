SESSION_STATE      = "session:{session_id}:state"            # HASH (json string)
CURRENT_QUESTION   = "session:{session_id}:current_question" # STRING (int)
SESSION_QUESTIONS  = "session:{session_id}:questions"        # STRING (json list)
SESSION_ANSWERS    = "session:{session_id}:answers:{qidx}"   # HASH player_id -> json(selected_options, ts)
PLAYERS            = "session:{session_id}:players"          # HASH player_id -> json(nickname, score)
QUESTION_TIMER_TASK= "session:{session_id}:timer_task"       # STRING (optional)
META_PREFIX        = "session:{session_id}:meta"             # HASH for misc meta