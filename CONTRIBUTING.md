### General checklist

* Make sure your code is compliant to Coding guidelines section below.
* Git: A commit should only include the changes that are relevant to the issue being addressed in the commit.
* Git: Keep commit titles short and self-explanatory including the GitHub issue number (example: '#12') 
* Git: Include a commit description that elaborates:
 	  * What code changed
 	  * What was added or removed
* Testing: 
 	  * Make sure the fix fixes the bug in question
 	  * Run tests with `nosetests tests`
 	  * (if any) UI changes -- screenshot before and after, include in PR

### Coding guidelines

* Code should be PEP8 compliant but ignore E501, E128, E123, E124, E402
* For *.js and *.html, we use 2 spaces from margin
* For *.py, we use 2/4 spaces from margin