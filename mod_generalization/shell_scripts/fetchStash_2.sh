#!/bin/bash

mkdir -p stash_repo22
count=0
nid="198550917-205833824-194002748-223047931-209684808"
CURL_TPL="curl http://api.pathofexile.com/public-stash-tabs/?id=<ID> -o poestash_<DATE>-<COUNT>.json"
while  :
do
	
	 # ----------------------
	 # Save last requested id
	 # ----------------------
	 previousid=$nid

	 # ----------------------
	 # Download next_id
	 # ----------------------
	 DATE=`date '+%Y-%m-%d-%H-%M'`
	 echo "getting  stash id = $nid count =  $count"
	 echo $CURL_TPL | sed "s/<ID>/$nid/g"   | sed "s/<DATE>/$DATE/g"   | sed "s/<COUNT>/$count/g"    > f_nextstash.sh
	 chmod +x f_nextstash.sh
	 ./f_nextstash.sh
	 echo "Downloaded   stash id = $nid count =  $count"


	 # ----------------------
	 # parse next id
	 # ----------------------
	 nid=`cat poestash_$DATE-$count.json | jq '.next_change_id' `
	  
	 if [ -n "$nid" ] && [ "$nid" != "null" ] ; then
		# ---------------------------------------
		# all is good there is a valid nid 
		# ---------------------------------------
		mv "poestash_$DATE-$count.json" stash_repo22
		echo "$nid:poestash_$DATE-$count.json" >> stash_repo22/index22.csv

		echo "Next id = $nid"

		(( count++ ))	

	 else
		# ----------------------------
		# Fetch next id not successful
		# retry with last required id
		# ----------------------------
		nid=$previousid

		echo "Something went wrong! Nothing to save for next change id. Retrying : $nid"
		echo -e "\a"
		echo -e "\a"
		echo -e "\a"
	 fi

	 sleep 3 

done
