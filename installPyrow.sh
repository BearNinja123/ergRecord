sudo apt install libusb-dev
cd /tmp
git clone https://github.com/droogmic/Py3Row
cd Py3Row
python3 setup.py build
sudo python3 setup.py install
sudo cp 99-erg.rules /etc/udev/rules.d/
sudo systemctl restart udev
