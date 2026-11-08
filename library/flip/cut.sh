#!/bin/sh
# Cut, align and build one flipbook: sh library/flip/cut.sh NAME
set -e
cd "$(dirname "$0")/../.."
n=$1
eval "$(python3 -c "
import json
j=[x for x in json.load(open('library/flip/jobs.json')) if x['name']=='$n'][0]
print('grid=%s; seq=\"%s\"' % (j['grid'], j['seq']))")"
rm -f library/flip/$n/frame*.png library/flip/$n/frame*.json
python3 -I scripts/frames.py library/flip/$n/sheet.jpg library/flip/$n/frame --grid $grid > /dev/null
node scripts/flipbook.mjs library/flip/$n --seq "$seq" --title "$n" > /dev/null
node scripts/build.mjs library/flip/$n/scene.json --out library/flip/$n/anim.html > /dev/null
echo "$n: $(ls library/flip/$n/frame*.png | wc -l | tr -d ' ') frames"
