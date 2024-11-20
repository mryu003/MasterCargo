# Run the app
From `/MasterCargo` run 
```
flask --app website run --debug
```
# Test coverage
- If your are using virtual environment run `pytest`
- If your are NOT using virtual environment run `python -m pytest -vv`
## To see coverage report
- CLI run 
```
coverage run -m pytest
coverage report
```
- HTML report with covered lines of code
```
coverage html
```