mkdir -p indexes
 
previousid=""
count=0
while  :
do
	DATE=`date '+%Y-%m-%d-%H-%M'`

	tries=0
	while [ $tries -lt 3 ]
	do
 		 rm -f change_ids.json
		 echo "getting  next change id from api no = $count "
		 curl -s https://www.pathofexile.com/api/trade/data/change-ids -o change_ids.json .. /dev/null
		 nid=`jq '.psapi' change_ids.json  | sed 's/\"//g'`
		  
		 if [ -z "$nid" ]; then
			(( tries++ ))	
			echo -e "\a"
		 elif [ "$previousid" == "$nid" ] ; then 
			(( tries++ ))	
			echo "previous id = nid --> No change ($previousid ** $nid)"
			echo "Sleeping zzzzzzzzzzzzzzzzzz"
			sleep 2
		 else
			echo " (P: $previousid ** N: $nid)"
			echo "next change id : $nid"
			echo "$nid:$DATE" >> next_change_ids_idx.csv
			previousid=$nid
			(( count++ ))
			break
		 fi

	done
done
