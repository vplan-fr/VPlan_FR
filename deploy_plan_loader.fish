#!/usr/bin/fish

# Kill the existing process if it is running
if kill -INT (lsof -t nohup.out)
    echo "=> Sent kill signal to the running plan loader..."

    # Wait for the process to exit
    while lsof -t nohup.out
        sleep 1
        echo " -> Waiting for exit..."
    end
else
    echo "=> No plan loader running."
end

# Remove existing nohup.out
echo "=> Removing existing nohup.out..."
if rm -f nohup.out
    echo " -> Success"
else
    echo " -> No existing nohup.out file. (or error)"
end

echo "=> Removing existing nohup.out2..."
if rm -f nohup.out2
    echo " -> Success"
else
    echo " -> No existing nohup.out2 file. (or error)"
end

# Start the plan loader
echo "=> Starting plan loader..."
nohup venv/bin/python3 -m backend.load_plans --ignore-exceptions --never-raise-out-of-proxies -l DEBUG -i 300 > nohup.out2 2> nohup.out < /dev/null &

# Disown the process
echo "=> Disowning..."
disown (lsof -t nohup.out)

echo "=> Done!"
