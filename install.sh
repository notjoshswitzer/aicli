echo python3 $PWD/ai.py '"$@"' > /bin/ai
chmod +x /bin/ai
echo -e "\nPlease ensure you have the following python3 packages installed"
echo "- requests"
echo "- rich"
