PY=pipenv run python3
default: runsm
.SILENT: precomp

precomp:
	@$(PY) -m compileall .

run: 
	$(PY) ./langex.py

runsm: 
	$(PY) ./langex.py -sm

clean:
	rm -f ./*.csv