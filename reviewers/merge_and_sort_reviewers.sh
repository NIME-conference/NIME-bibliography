cat reviewers_NIME* | sort > reviewers_all.txt
uniq -c reviewers_all.txt | sort -nr > reviewers_count.txt
