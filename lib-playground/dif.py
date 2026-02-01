import difflib



with open('test.py', 'r') as f:
    file_1_content = f.read()

with open('test2.py', 'r') as f:
    file_2_content = f.read()


original_lines = file_1_content.splitlines(keepends=True)
edited_lines = file_2_content.splitlines(keepends=True)

diff = difflib.unified_diff(
    original_lines,
    edited_lines,
    fromfile='test.py (original)',
    tofile='test_2.py (edited)',
    lineterm=''
)

print('\n'.join(diff))