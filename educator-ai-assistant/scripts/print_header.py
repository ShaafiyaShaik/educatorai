with open('recovered_72570f92.sqlite','rb') as f:
    b=f.read(64)
print(b[:16])
print(b[:16].hex())
print(repr(b[:16]))
