def chunk(values, n):
  for i in range(0, len(values), n):
    yield values[i:i + n]