PID=`ps -C 'python3' -o pid=`
kill -9 $PID
unset PID

