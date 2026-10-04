#!/bin/bash
# Survey of the same-day cycle over committed snapshots (no commits, no pull requests). For each <date>:<snapshot csv>, the pipeline runs with
# --force --no-publish (plus the mode after `--`: `--survey` = regeneration, Gate 1b and the pre-check only; `--exercise` = every stage) in a
# fresh copy of the tree at <pipeline_sha>, with data/calibrations of <main_sha> copied in (main carries only calibration snapshots beyond the
# pipeline base, so this is the tree a same-day `prepare` would produce). From the repl:
#   c = host.compute.create('modal', provider_params={'image': 'im-yxBt8u8Ao1kVKCITcVzwk7', 'cpu': 8, 'memory': 32768, 'timeout': 5400,
#                                                     'volumes': {'/vol': '<volume>'}})
#   c.submit_job(command='bash run_survey.sh <pipeline_sha> <main_sha> 2026-09-29:ibm_phoenix_2026-09-29T030852Z.csv ... -- --survey --workers 12',
#                inputs=['modal/run_survey.sh'], run_timeout_s=4500, intent='same-day survey')
# Outputs: out/survey/<date>/{run.log, EXIT, <date>_summary.json / .md, bundle.tgz} (and the same under /vol/survey/<date>/ when a Volume is
# mounted); then c.close().
set -u
SHA=$1; MAIN=$2; shift 2
WORK=$PWD
mkdir -p $WORK/out/survey
python - "$SHA" "$MAIN" <<'EOF'
import io, sys, urllib.request, zipfile
for sha in dict.fromkeys(sys.argv[1:]):
    d = urllib.request.urlopen(f"https://codeload.github.com/SSIT-Q/gradvar-phoenix/zip/{sha}", timeout=900).read()
    zipfile.ZipFile(io.BytesIO(d)).extractall("/tmp/src")
EOF
BASE=/tmp/src/gradvar-phoenix-$SHA
cp /tmp/src/gradvar-phoenix-$MAIN/data/calibrations/* $BASE/data/calibrations/ || exit 3
DAYS=(); EXTRA=()
while [ $# -gt 0 ]; do
  if [ "$1" = "--" ]; then shift; EXTRA=("$@"); break; fi
  DAYS+=("$1"); shift
done
for DS in "${DAYS[@]}"; do
  D=${DS%%:*}; CSV=${DS#*:}
  T0=$(date +%s)
  TREE=/tmp/survey/$D; RUN=/tmp/survey_out/$D; OUT=$WORK/out/survey/$D      # work files stay in /tmp; only small results under out/
  rm -rf $TREE $RUN; mkdir -p /tmp/survey $RUN $OUT; cp -r $BASE $TREE
  (cd $TREE && PYTHONHASHSEED=0 GRADVAR_COMMIT=$SHA python scripts/sameday_repackage.py run --no-modal --run-sha $SHA --base-sha $SHA \
      --snapshot data/calibrations/$CSV --date $D --with-pairs --force --no-publish --t0 $T0 --cost-cores ${COST_CORES:-32} \
      --cost-mem-gib ${COST_MEM_GIB:-64} --out $RUN --bundle $OUT/bundle.tgz ${EXTRA[@]+"${EXTRA[@]}"} > $OUT/run.log 2>&1)
  echo "exit $?" > $OUT/EXIT
  cp $TREE/docs/repack/${D}_summary.json $TREE/docs/repack/${D}_summary.md $OUT/ 2>/dev/null
  if [ -d /vol ]; then mkdir -p /vol/survey/$D && cp -r $OUT/. /vol/survey/$D/ && sync; fi   # durable copy when a Volume is mounted
  echo "== $D: $(tail -n 1 $OUT/run.log)"
done
exit 0
