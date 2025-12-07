
echo "Shell Check:" > verification.txt
echo $0 >> verification.txt
echo "Node Check:" >> verification.txt
node -v >> verification.txt 2>&1
echo "PowerShell Check:" >> verification.txt
echo $PSVersionTable >> verification.txt
