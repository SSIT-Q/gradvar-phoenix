import io, os, subprocess, sys, time, urllib.request, zipfile
SHA = "f11dc7aa831bc2c55522a182a2f22a919b129bc8"
stage, workers = sys.argv[1], sys.argv[2]
t0 = time.time()
data = urllib.request.urlopen(f"https://codeload.github.com/SSIT-Q/gradvar-phoenix/zip/{SHA}", timeout=300).read()
zipfile.ZipFile(io.BytesIO(data)).extractall("/tmp/src")
root = f"/tmp/src/gradvar-phoenix-{SHA}"
os.makedirs("out", exist_ok=True)
open("out/" + stage + "__source.txt", "w").write(f"repo SSIT-Q/gradvar-phoenix commit {SHA} (codeload zip, {len(data)} bytes); fetched+extracted in {time.time()-t0:.0f}s\n")
env = dict(os.environ, PYTHONPATH=root + os.pathsep + root + "/scripts", GRADVAR_COMMIT=SHA)
sys.exit(subprocess.call([sys.executable, "drift_driver.py", "--root", root, "--out", os.path.abspath("out"), "--stage", stage, "--workers", workers] + (["--part", sys.argv[3]] if len(sys.argv) > 3 else []), env=env))
