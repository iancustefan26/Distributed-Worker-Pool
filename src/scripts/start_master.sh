echo "Starting master node..."
echo "Ruunig apt-get update --fix-missing"
apt-get update --fix-missing

# echo "Installing Playwright browsers..."
# playwright install --with-deps

python -m src.master.main