def yield_lines():
    headers = None

    with open('MathOperationsTable.txt', 'r') as f_in:
        for index, line in enumerate(f_in):
            if headers is None:
                names = line.split(', ')
                headers = []
                for name in names:
                    headers.append(name.strip())
                    if name == 'Index':
                        headers.append('Time')
                yield ', '.join(headers)
                continue
            their_cols = line.split('\t')
            real_columns = []
            time = None
            for double_wide in their_cols:
                try:
                    left, right = double_wide.split(',')
                except ValueError:
                    if double_wide == str(int(double_wide)):
                        left = None
                        right = double_wide
                    else:
                        raise
                if time is None and left is not None:
                    time = True
                    real_columns.append(left.strip())
                real_columns.append(right.strip())
            yield ', '.join(real_columns)

with open('MathOperationsTable.csv', 'w') as f_out:
    for index, line in enumerate(yield_lines()):
        f_out.write(line + '\n')
        if index % 1000 == 0:
            print('done with line %d' % (index,))
