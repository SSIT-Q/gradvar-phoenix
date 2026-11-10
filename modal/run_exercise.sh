#!/bin/bash
# Exercise of the same-day cycle on a committed snapshot whose lists are already on the tree (pipeline tests only; nothing is written to any branch).
# From the repl, as modal/run_sameday.sh:
#   c.submit_job(command='bash run_exercise.sh <run_sha> <lists_sha> <tag> --snapshot data/calibrations/<csv> --with-pairs --force --force-reason exercise',
#                inputs=['modal/run_exercise.sh'], run_timeout_s=4800, intent='same-day exercise')
# <run_sha>:   the commit of the pipeline under test (codeload zip).
# <lists_sha>: an earlier commit whose un-armed lists stand for "the previous package" (placed on an earlier snapshot). Only lists that are NOT run
#              records at <run_sha> are restored from it: a record is never replaced (scripts/run_records.py decides, no names here).
# <tag>:       the prediction tag of the snapshot under exercise (YYYY-MM-DDTHHMM); the committed prediction files of that tag are removed from the
#              sandbox tree, so that every re-draw and every comparator is drawn as on a real day (the bundle then holds them for a comparison with
#              the committed files).
# The run uses --exercise: a Gate 1b FAIL or a comparator stop is recorded and the remaining stages still run. The bundle is never published for dispatch.
set -u
SHA=$1; LISTS_SHA=$2; TAG=$3; shift 3
WORK=$PWD
T0=$(date +%s)
mkdir -p $WORK/out/sameday
python - "$SHA" "$LISTS_SHA" <<'EOF'
import io, sys, urllib.request, zipfile
for sha, dst in ((sys.argv[1], "/tmp/src"), (sys.argv[2], "/tmp/prev")):
    d = urllib.request.urlopen(f"https://codeload.github.com/SSIT-Q/gradvar-phoenix/zip/{sha}", timeout=900).read()
    z = zipfile.ZipFile(io.BytesIO(d))
    z.extractall(dst, members=[m for m in z.namelist() if dst == "/tmp/src" or "/data/joblists/paper1/" in m])
EOF
cd /tmp/src/gradvar-phoenix-$SHA || exit 3
python - "$LISTS_SHA" "$TAG" > $WORK/out/sameday/exercise_setup.log 2>&1 <<'EOF'
import json, shutil, sys
from pathlib import Path
sys.path.insert(0, "scripts")
import run_records as RR
prev, tag = Path(f"/tmp/prev/gradvar-phoenix-{sys.argv[1]}/data/joblists/paper1"), sys.argv[2]
here = Path("data/joblists/paper1")
recs = set(RR.records_in(here))
for p in sorted(prev.glob("*.json")):
    if p.stem in recs:
        print("kept (run record):", p.name)
        continue
    shutil.copyfile(p, here / p.name)
    print("restored from the earlier commit:", p.name, json.loads(p.read_text()).get("placement", {}).get("stamp") if p.stem != "summary" else "")
for p in sorted(Path("data/predictions").glob(f"*_{tag}.*")):
    shutil.move(str(p), f"/tmp/committed_{p.name}")
    print("set aside (committed prediction file of the exercised tag):", p.name)
RR.require_consistent(here)
EOF
export PYTHONHASHSEED=0 GRADVAR_COMMIT=$SHA
python scripts/sameday_repackage.py run --no-modal --exercise --run-sha $SHA --t0 $T0 --cost-cores ${COST_CORES:-32} --cost-mem-gib ${COST_MEM_GIB:-64} \
    --out $WORK/out/sameday --bundle $WORK/out/sameday/bundle.tgz "$@" > $WORK/out/sameday/run.log 2>&1
RC=$?
echo "exit $RC" > $WORK/out/sameday/EXIT
# what the exercise re-drew against the committed files of the same tag (byte comparison of the CSV files; the JSON / md files carry run times)
python - "$TAG" > $WORK/out/sameday/reproduction.json 2>&1 <<'EOF'
import hashlib, json, sys
from pathlib import Path
tag, out = sys.argv[1], {}
for p in sorted(Path("/tmp").glob(f"committed_*_{tag}.*")):
    new = Path("data/predictions") / p.name[len("committed_"):]
    out[new.name] = dict(redrawn=new.exists(), identical=new.exists() and hashlib.sha256(new.read_bytes()).hexdigest() == hashlib.sha256(p.read_bytes()).hexdigest())
print(json.dumps(out, indent=1))
EOF
mkdir -p $WORK/out/sameday/dry && cp $WORK/out/sameday/A/dryrun_*.log $WORK/out/sameday/dry/ 2>/dev/null
tail -n 30 $WORK/out/sameday/run.log
exit 0
