
# kill clients, bots, and server processes
# from the filename python is running
# cf http://unix.stackexchange.com/questions/5717/bash-script-to-find-and-kill-a-process-with-certain-arguments

# TODO: accept 'bot', 'cli', 'srv', and 'all' arguments 

pkill -f "cc-srv.py"
pkill -f "cc-cli.py"
pkill -f "cc-bot.py"

