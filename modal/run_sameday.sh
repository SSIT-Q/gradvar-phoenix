#!/bin/bash
# Same-day re-package in one Modal sandbox through host.compute (Claude Science). From the repl:
#   c = host.compute.create('modal', provider_params={'image': 'im-yxBt8u8Ao1kVKCITcVzwk7', 'cpu': 32, 'memory': 65536, 'timeout': 5400})
#   c.submit_job(command='bash run_sameday.sh <run_sha> --base-sha <base_sha> [--date YYYY-MM-DD] [--snapshot data/calibrations/X.csv] [--with-pairs]',
#                inputs=['modal/run_sameday.sh'], run_timeout_s=4800, intent='same-day re-package')
# <run_sha>: the commit printed by `python scripts/sameday_repackage.py prepare --date D --base <pipeline branch>` (repack-<date> with main merged in).
# Afterwards, with GITHUB_TOKEN: python scripts/sameday_repackage.py publish --bundle hpc/<job id>/out/sameday/bundle ; then c.close().
set -u
SHA=$1; shift
WORK=$PWD
T0=$(date +%s)
mkdir -p $WORK/out/sameday
python - "$SHA" <<'EOF'
import io, sys, urllib.request, zipfile
sha = sys.argv[1]
d = urllib.request.urlopen(f"https://codeload.github.com/SSIT-Q/gradvar-phoenix/zip/{sha}", timeout=900).read()
zipfile.ZipFile(io.BytesIO(d)).extractall("/tmp/src")
EOF
cd /tmp/src/gradvar-phoenix-$SHA || exit 3
export PYTHONHASHSEED=0 GRADVAR_COMMIT=$SHA
python scripts/sameday_repackage.py run --no-modal --run-sha $SHA --t0 $T0 --cost-cores ${COST_CORES:-32} --cost-mem-gib ${COST_MEM_GIB:-64} \
    --out $WORK/out/sameday --bundle $WORK/out/sameday/bundle.tgz "$@" > $WORK/out/sameday/run.log 2>&1
RC=$?
echo "exit $RC" > $WORK/out/sameday/EXIT
tail -n 30 $WORK/out/sameday/run.log
exit 0
