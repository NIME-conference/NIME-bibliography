echo "# NIME Reviewers" > reviewers_all_years.md
for fname in $(ls -r *.txt); do
  echo " " >> reviewers_all_years.md
  extracted=$(echo $fname | cut -d_ -f2 2>/dev/null | cut -d. -f1 2>/dev/null)
  shortened=${extracted//NIME/}
  echo "### $shortened" >> reviewers_all_years.md
  echo " " >> reviewers_all_years.md
  awk '{if (NR>1) print prev ","; prev=$0} END {if (NR>0) print prev}' "$fname" >> reviewers_all_years.md
done