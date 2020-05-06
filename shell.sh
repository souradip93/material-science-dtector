memory=`nvidia-smi | awk '/Default/ {print $9}'`
memory=${memory::-3}
memory=$(( memory ))

while [ "$memory" -gt 6000 ]
do
done

nohup python manage.py 0.0.0.0:8000 &

echo $memory
