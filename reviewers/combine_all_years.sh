echo "# NIME Reviewers" > reviewers_all_years.md
for fname in *.txt; do
  echo " " >> reviewers_all_years.md ;
  echo " ## " $fname | cut -d_ -f2 | cut -d. -f1 >> reviewers_all_years.md ;
  echo " " >> reviewers_all_years.md ;
  cat $fname >> reviewers_all_years.md ;
done
