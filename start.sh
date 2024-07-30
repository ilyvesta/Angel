if [ -z $UPSTREAM_REPO ]
then
  echo "Cloning main Repository"
  git clone https://github.com/ilyvesta/Angel.git /Angel
else
  echo "Cloning Custom Repo from $UPSTREAM_REPO "
  git clone $UPSTREAM_REPO /Angel 
fi
cd /hey_tess
pip3 install -U -r requirements.txt
echo "Starting Angel...."
python3 bot.py
