#!/bin/sh
# r05: hash outputs, rerun pipeline/impacts/08_owens2018.py once, hash again. Run from final/.
R=audits/owens2018/recheck_2026-10-04/results
shasum -a 256 data/derived/impacts/owens2018_results.json data/derived/impacts/owens2018_pdftext.txt > $R/r05_sha_before.txt
python3 pipeline/impacts/08_owens2018.py > $R/r05_rerun_stdout.txt 2>&1; echo "exit=$?" >> $R/r05_rerun_stdout.txt
shasum -a 256 data/derived/impacts/owens2018_results.json data/derived/impacts/owens2018_pdftext.txt > $R/r05_sha_after.txt
cmp $R/r05_sha_before.txt $R/r05_sha_after.txt && echo IDENTICAL
