#!/bin/bash
# Survey of the same-day cycle over committed snapshots (no commits, no pull requests). For each <date>:<snapshot csv>, the pipeline runs in
# --exercise --force --no-publish mode in a fresh copy of the tree at <pipeline_sha>, with data/calibrations of <main_sha> copied in (main carries
# only calibration snapshots beyond the pipeline base, so this is the tree a same-day `prepare` would produce). From the repl:
#   c = host.compute.create('modal', provider_params={'image': 'im-yxBt8u8Ao1kVKCITcVzwk7', 'cpu': 32, 'memory': 65536, 'timeout': 5400})
#   c.submit_job(command='bash run_survey.sh <pipeline_sha> <main_sha> 2026-09-29:ibm_phoenix_2026-09-29T030852Z.csv ... [-- extra run args]',
#                inputs=['modal/run_survey.sh'], run_timeout_s=3600, intent='same-day survey')
# Outputs: out/survey/<date>/{run.log, EXIT, bundle/ (summary JSON / md, lists, predictions, pre-flights), bundle.tgz}; then c.close().
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
  TREE=/tmp/survey/$D; OUT=$WORK/out/survey/$D
  rm -rf $TREE; mkdir -p /tmp/survey $OUT; cp -r $BASE $TREE
  (cd $TREE && PYTHONHASHSEED=0 GRADVAR_COMMIT=$SHA python scripts/sameday_repackage.py run --no-modal --run-sha $SHA --base-sha $SHA \
      --snapshot data/calibrations/$CSV --date $D --with-pairs --exercise --force --no-publish --t0 $T0 --cost-cores ${COST_CORES:-32} \
      --cost-mem-gib ${COST_MEM_GIB:-64} --out $OUT --bundle $OUT/bundle.tgz ${EXTRA[@]+"${EXTRA[@]}"} > $OUT/run.log 2>&1)
  echo "exit $?" > $OUT/EXIT
  echo "== $D: $(tail -n 1 $OUT/run.log)"
done
exit 0
