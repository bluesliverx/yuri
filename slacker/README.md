# Slacker Blocks Fork

This is cloned from https://github.com/symroe/slacker, 
which is a forked version with blocks support for the slack API.

This also needs a patch to the `__init__.Chat.post_message` method:

```
# Ensure blocks are json encoded**
if blocks:
    if isinstance(blocks, list):
        blocks = json.dumps(blocks)
```
