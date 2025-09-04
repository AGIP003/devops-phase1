set -euo pipefail

echo "Good evening, $USER"
echo "The date today is: $(date)"
echo "Kindly key in a number:"
read num
count=1
while [ $count -le $num ]
do
echo "Count: $count"
((count++))
done

