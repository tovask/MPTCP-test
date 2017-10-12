# creating a virtual Ubuntu (14.04) on AWS EC2 (t2.micro)

# install MPTCP
sudo apt-key adv --keyserver hkp://keys.gnupg.net --recv-keys 379CE192D401AB61
sudo echo -e "\n\n# for MPTCP\ndeb https://dl.bintray.com/cpaasch/deb jessie main\n" >> /etc/apt/sources.list
sudo apt-get update
sudo apt-get install linux-mptcp
# reboot
sudo reboot
# verify
dmesg | grep MPTCP
sysctl net.mptcp

# install mininet
sudo apt-get install git
git clone git://github.com/mininet/mininet
mininet/util/install.sh -a
# test
sudo mn --test pingall
