raspberry pi version is from 
http://www.sensorsiot.org/pimp-my-raspberry-pi-3/



=================auto run=================

chmod 755 launcher.sh

Navigate back to your home directory:
cd
Create a logs directory:
mkdir logs

sudo crontab -e    (select ¡°nano editor¡± if asked)

Fill in:
@reboot sh /home/pi/Scripts/launcher.sh >/home/pi/logs/cronlog 2>&1


If it doesn't work, check out the log file:

cd logs
cat cronlog