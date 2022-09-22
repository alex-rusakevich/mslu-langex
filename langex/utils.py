import datetime


def log(*args, **kwargs):
    print(f"[{datetime.datetime.now()}]", *args, **kwargs)


def done():
    print("Done.")


def remove_column_from_matrix(matrix, i):
    new_mat = []

    for row in matrix:
        row.pop(i)
        new_mat.append(row)

    return new_mat
