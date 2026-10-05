"""Exponential backoff with full jitter (Brooker, AWS Architecture Blog, 2015): sleep a random
time between 0 and min(cap, base * 2**attempt). Seeded so the output is reproducible."""
import random

def full_jitter(attempt, base=1.0, cap=60.0, rng=random.Random(7)):
    return rng.uniform(0, min(cap, base * 2 ** attempt))

print("attempt  ceiling  full-jitter wait (s)")
for a in range(7):
    print(f"{a:>7}  {min(60.0, 2 ** a):>7.0f}  {full_jitter(a):>8.2f}")
total = sum(min(60.0, 2 ** a) for a in range(7))
print(f"worst case before giving up: {total:.0f} s")
