#Check if user exists, 
if ! id "devops" &>/dev/null; then
echo "Creating devops user..."
sudo adduser --disabled-password --gecos "" devops
else
echo "User devops already exists"
fi

echo "creating a secure directory.."
sudo mkdir -p /home/devops/secure/
sudo chown devops:devops /home/devops/secure/
sudo chmod 700 /home/devops/secure/ # Only devops can access

echo "Creating a secrets file..."
sudo touch /home/devops/secure/secrets.txt
sudo chown devops:devops home/devops/secure/secrets.txt
sudo chmod 600 /home/devops/secure/secrets.txt

echo "Secure area prepared for devops"
