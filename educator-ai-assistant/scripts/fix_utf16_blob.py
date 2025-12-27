# Convert a UTF-16LE-ified binary blob back to original bytes by taking low bytes
import sys
p_in = 'recovered_72570f92.sqlite'
p_out = 'fixed_recovered_72570f92.sqlite'
with open(p_in, 'rb') as f:
    b = f.read()
# if BOM for UTF-16 LE
if len(b) >= 2 and b[0] == 0xFF and b[1] == 0xFE:
    b = b[2:]
# take every 2nd byte (low bytes)
fixed = b[0::2]
with open(p_out, 'wb') as f:
    f.write(fixed)
print('wrote', p_out, 'size', len(fixed))
# quick check: print header
print('header:', fixed[:16])
