with open("all_digits.txt", "r") as f:
    raw = f.read()

snippet = raw[86400:88800]
print(snippet)
