sudo apt install portaudio19-dev
apt install xvfb

curl -o vimium-master.zip -L https://github.com/philc/vimium/archive/refs/heads/master.zip
unzip vimium-master.zip
rm vimium-master.zip

playwright install --with-deps

conda activate py_oca
pip install -r requirements.txt