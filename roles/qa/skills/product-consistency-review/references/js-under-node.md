# Testing window JS logic under node (from pytest)

Use this when a rule lives in a vanilla `app.js` with no module system, and a
test that only checks the source text would not prove the rule.

1. **Make the rule a pure top-level function.** If the logic sits inline in a
   render loop (for example, which key goes to which answer button), pull it out
   into `function answerKeys(it) { ... }`. The render loop and the test then
   read the same list, so the test cannot pass while the screen does
   something else.
2. **Extract the source in the test.** Take it from `function name(` up to the
   first `"\n}\n"`. That works only because the function is top-level and
   closes at column 0.
3. **Stub only the globals the functions touch** (e.g. `const REAL = new
   Set([...]); const rv = { learned: {} };`), then join the stubs and the
   extracted functions with a driver.
4. **Run the driver.** Feed the item as JSON on stdin and print JSON from the
   functions:

```python
NODE = shutil.which("node")
needs_node = pytest.mark.skipif(NODE is None, reason="node is not installed")

code = stubs + src + (
    "const it = JSON.parse(require('fs').readFileSync(0, 'utf8'));"
    "process.stdout.write(JSON.stringify({asked: askedOf(it)}));")
r = subprocess.run([NODE, "-e", code], input=json.dumps(item),
                   capture_output=True, text=True, encoding="utf-8", check=True)
```

5. **Feed it real data.** Build the item with the real CLI (`review --json`)
   from a temp database, not by hand. Then the JS is tested against the real
   data shape, and a renamed field fails the test.
6. **Keep one source-text test** for things node cannot see. For example,
   assert that the old field name (`is_primary`) no longer appears in the file.

Never install node for this. Skip with `needs_node` when it is absent.
