
@InspectLineage
def do_join():
    df = df1.select('a').groupby('c')
    df3 = df.sum()
    df4 = df3.join(df1)
    return df4


do_join()

